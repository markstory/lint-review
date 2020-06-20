import re
import os
import logging
import hashlib
from typing import Dict, List, Optional  # noqa: F401

import docker
from docker.errors import (
    ImageNotFound,
    APIError,
    NotFound
)
from requests.exceptions import ReadTimeout, ConnectionError

log = logging.getLogger(__name__)
buildlog = logging.getLogger('buildlog')

# The base path for all docker operations
DOCKER_BASE = '/src'
CUSTOM_IMAGE_PATTERN = re.compile(r'^\w+-[a-f0-9]+$')


class TimeoutError(Exception):
    """Exception for when we timeout waiting for docker."""


def _get_client(timeout=60):
    # type: () -> docker.DockerClient
    """Get a docker client."""
    return docker.from_env(timeout=timeout)


def replace_basedir(base, files):
    """Replace `base` with the docker base path"""
    out = []
    baselen = len(base)
    for path in files:
        if path.startswith(base):
            path = path[baselen:].lstrip(os.sep)
        path = os.path.join(DOCKER_BASE, path)
        out.append(path)
    return out


def strip_base(path):
    """Remove the docker base path from a path

    Some linters include absolute paths in their outputs.
    We need to strip the base path off to match files with
    those in the diff.
    """
    if path.startswith(DOCKER_BASE):
        return path[len(DOCKER_BASE) + 1:]
    return path


def apply_base(value):
    path = os.path.abspath(os.path.join(DOCKER_BASE, value))
    if path.startswith(DOCKER_BASE):
        return path
    if path == '/':
        return DOCKER_BASE
    return os.path.basename(value)


def image_exists(name):
    # type: (str) -> bool
    """Check if a docker image exists."""
    client = _get_client()
    try:
        client.images.get(name)
    except ImageNotFound:
        return False
    return True


def images():
    # type: () -> List[str]
    """Get the docker image list."""
    client = _get_client()
    results = []
    for image in client.images.list():
        results += image.tags
    return results


def containers(include_stopped=False):
    # type: (bool) -> List[str]
    """Get the container list"""
    client = _get_client()
    results = []
    d_containers = client.containers.list(all=include_stopped)
    for container in d_containers:
        results.append(container.name)

    return results


def run(image,                     # type: str
        command,                   # type: List[str]
        source_dir,                # type: str
        env=None,                  # type: Dict[str, str]
        timeout=300,               # type: Optional[int]
        name=None,                 # type: Optional[str]
        docker_base=None,          # type: Optional[str]
        workdir=None,              # type: Optional[str]
        include_error=True,        # type: bool
        run_as_current_user=False  # type: bool
        ):
    # type: (...) -> str
    """Execute tool commands in docker containers.

    All output from the container will be treated as tool output
    to be parsed by the tool adapter.

    The source_dir will be mounted at `/src` in the container
    for tool execution.
    """
    if not docker_base:
        docker_base = DOCKER_BASE

    run_args = {
        'image': image,
        'command': [str(c) for c in command],
        'environment': env,
        'volumes': {source_dir: {'bind': docker_base, 'mode': 'rw'}},
        'stdout': True,
        'stderr': include_error,
        'detach': True,
    }

    if name is not None:
        run_args['name'] = name

    if workdir:
        run_args['working_dir'] = workdir

    if run_as_current_user:
        run_args['user'] = os.getuid()

    if CUSTOM_IMAGE_PATTERN.match(image):
        buildlog.info('Using custom image %s', image)

    # Only log the first 15 parameters.
    buildlog.info('Running container: %s', u' '.join(run_args['command'][0:15]))
    client = _get_client()
    try:
        container = client.containers.run(**run_args)
    except ImageNotFound:
        err_txt = "Image not found."
        log.exception(err_txt)
        return err_txt
    except APIError:
        log.exception("API Error running container.")
        return "API Error Running Container."

    try:
        container.wait(timeout=timeout)
        output = b''
        if include_error:
            output += container.logs(stdout=False, stderr=True)
        output += container.logs(stdout=True, stderr=False)
    except (APIError, ReadTimeout, ConnectionError) as e:
        log.error("%s container timed out error=%s.", image, e)
        raise TimeoutError(str(e))
    finally:
        if name is None:
            container.remove(v=True, force=True)

    return output.decode('utf8')


def rm_container(name):
    # type: (str) -> None
    """Remove a container with the provided name."""
    client = _get_client()
    try:
        container = client.containers.get(name)
        container.remove(v=True, force=True)
    except (NotFound, APIError):
        log.exception("Error removing container.")
        raise ValueError("Unable to remove container.")


def rm_image(name):
    # type: (str) -> None
    """Remove the named image with the provided name."""
    client = _get_client()
    try:
        client.images.remove(image=name, force=True)
    except ImageNotFound:
        log.exception("Image: %s wasn't found, but we tried to remove it.",
                      name)
        raise ValueError("Could not remove: {0}".format(name))


def commit(name, timeout=120):
    # type: (str) -> None
    """Commit a container state into a new images."""
    client = _get_client(timeout=timeout)
    log.info('Commiting new image for %s', name)
    try:
        container = client.containers.get(name)
        container.commit(repository=name)
    except (NotFound, APIError):
        log.exception("Exception committing container.")
        raise ValueError("Could not commit container: {0}".format(name))


def generate_container_name(prefix, files):
    m = hashlib.md5()
    m.update('-'.join(files).encode('utf8'))
    return prefix + m.hexdigest()
