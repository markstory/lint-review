import os
import logging
import shutil
import subprocess
from urlparse import urlparse, urlunparse

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
    path = path.rstrip('/')
    path = os.path.join(path, user, repo, str(number))
    return os.path.realpath(path)


def private_clone(config, url, path):
    # Add auth to url
    parsed_url = urlparse(url)
    if 'GITHUB_OAUTH_TOKEN' in config:
        user = config['GITHUB_OAUTH_TOKEN']
        password = 'x-oauth-basic'
    else:
        user = config['GITHUB_USER']
        password = config['GITHUB_PASSWORD']
    url = urlunparse((
        parsed_url[0], ('%s:%s@%s' % (user, password, parsed_url[1]))
    ) + parsed_url[2:])
    clone(url, path)


def clone(url, path):
    """
    Clone a repository from `url` into `path`
    """
    command = ['git', 'clone', url, path]
    return_code = _process(command)
    if return_code:
        log.error("Cloning '%s' repository failed", url)
        raise IOError("Unable to clone repository '%s'" % (url, ))
    return True


def fetch(path, remote):
    """
    Run git fetch on a repository
    """
    command = ['git', 'fetch', remote]
    return_code = _process(command, chdir=path)
    if return_code:
        log.error("Updating '%s' failed.", path)
        raise IOError("Unable to fetch new changes '%s'" % (path, ))
    return True


def clone_or_update(config, url, path, head, private=False):
    """
    Clone a new repository and checkout commit,
    or update an existing clone to the new head
    """
    log.info("Cloning/Updating repository '%s' into '%s'", url, path)
    if exists(path):
        log.debug("Path '%s' does exist, updating existing clone.", path)
        fetch(path, 'origin')
    else:
        log.debug('Repository does not exist, cloning a new one.')
        if not private:
            clone(url, path)
        else:
            private_clone(config, url, path)
    log.info("Checking out '%s'", head)
    checkout(path, head)


def checkout(path, ref):
    """
    Check out `ref` in the repo located on `path`
    """
    command = ['git', 'checkout', ref]
    return_code = _process(command, chdir=path)
    if return_code:
        log.error("Checking out '%s' failed", ref)
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
        path = os.path.join(path, '.git')
        log.debug("Checking for path '%s'", path)
        os.stat(path)
        return True
    except:
        log.debug('Path does not exist, or .git dir was missing')
        return False


def _process(command, chdir=False):
    """
    Helper method for running processes related to git.
    """

    if chdir:
        log.debug('Changing directories to %s', chdir)
        cwd = os.getcwd()
        os.chdir(chdir)

    log.debug('Running %s', command)

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False)
    return_code = process.wait()

    if chdir:
        os.chdir(cwd)
    if return_code > 0:
        log.error('STDERR output: %s', process.stderr.read())

    return return_code
