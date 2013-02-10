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
        raise IOError("Unable to clone repository '%s'" % (url, ))
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
