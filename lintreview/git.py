import os
import logging
import shutil
import subprocess

log = logging.getLogger(__name__)


def get_repo_path(user, repo, number, settings):
    """
    Get the target path a repo should be cloned into for the parameters.
    """
    try:
        path = settings['WORKSPACE']
    except:
        raise KeyError("You have not defined the WORKSPACE config"
                       " option. This is required for lintreview to work.")
    path = path.strip('/')
    path = os.path.join(path, user, repo, str(number))
    return os.path.realpath(path)


def clone(url, path):
    """
    Clone a repository from `url` into `path`
    """
    command = ['git', 'clone', url, path]
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False)
    return_code = process.wait()
    if return_code:
        log.error("Cloning '%s' repository failed", url)
        log.error(process.stderr.read())
        raise IOError("Unable to clone repository '%s'" % (url, ))
    return True


def fetch(path, remote):
    """
    Run git fetch on a repository
    """
    command = ['git', 'fetch', remote]
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False)
    return_code = process.wait()
    if return_code:
        log.error("Cloning '%s' repository failed", url)
        log.error(process.stderr.read())
        raise IOError("Unable to clone repository '%s'" % (url, ))
    return True


def clone_or_update(url, path, head):
    """
    Clone a new repository and checkout commit,
    or update an existing clone to the new head
    """
    log.info("Cloning/Updating repository '%s' into '%s'", url, path)
    if exists(path):
        log.debug("Path '%s' does not exist, cloning new copy.", path)
        fetch(path, 'origin')
    else:
        log.debug('Repository does not exist, cloning a new one.')
        clone(url, path)
    log.info("Checking out '%s'", head)
    checkout(path, head)


def checkout(path, ref):
    """
    Check out `ref` in the repo located on `path`
    """
    cwd = os.getcwd()
    os.chdir(path)
    command = ['git', 'checkout', ref]

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False)
    return_code = process.wait()
    os.chdir(cwd)

    if return_code:
        log.error("Checking out '%s' failed", ref)
        log.error(process.stderr.read())
        raise IOError("Unable to checkout '%s'" % (ref, ))
    return True


def destroy(path):
    """
    Blow up a repo and all its contents.
    """
    shutil.rmtree(path, False)


def exists(path):
    """
    Check if a path exists, and contains a git repo.

    returns false if either conditions is not true.
    """
    try:
        os.stat(os.path.join(path, '.git'))
        return True
    except:
        log.debug('Path does not exist, or .git dir was missing')
        return False
