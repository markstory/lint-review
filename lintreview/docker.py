from __future__ import absolute_import
import logging
import subprocess
from six.moves import map
import six
import os

log = logging.getLogger(__name__)

# The base path for all docker operations
DOCKER_BASE = '/src'


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
    """Check if a docker image exists"""
    process = subprocess.Popen(
        ['docker', 'images', '-q', name],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False)
    output, error = process.communicate()
    return len(output) > 0


def run(image, command, source_dir, env=None, timeout=None):
    """Execute tool commands in docker containers.

    All output from the container will be treated as tool output
    to be parsed by the tool adapter.

    The source_dir will be mounted at `/src` in the container
    for tool execution.
    """
    log.info('Running %s container', image)

    env_args = []
    if isinstance(env, dict):
        for key, val in env.items():
            env_args.extend(['-e', u'{key}={val}'.format(key=key, val=val)])
    elif env:
        raise ValueError('env argument should be a dict')

    # TODO add timeout support
    cmd = [
        'docker', 'run', '--rm',
        '-v', u'{}:{}'.format(source_dir, DOCKER_BASE)
    ]
    cmd += env_args
    cmd.append(image)
    cmd += list(map(six.text_type, command))

    log.debug('Running %s', ' '.join(cmd))
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True)

    output, error = process.communicate()
    output = error + output
    log.debug('Container output was: %s', output)

    return output
