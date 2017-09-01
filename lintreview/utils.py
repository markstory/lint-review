from __future__ import absolute_import
import os
import subprocess
import logging

log = logging.getLogger(__name__)


def in_path(name):
    """
    Check whether or not a command line tool
    exists in the system path.

    @return boolean
    """
    for dirname in os.environ['PATH'].split(os.pathsep):
        if os.path.exists(os.path.join(dirname, name)):
            return True
    return False


def npm_exists(name):
    """
    Check whether or not a cli tool exists in a node_modules/.bin
    dir in os.cwd

    @return boolean
    """
    cwd = os.getcwd()
    path = os.path.join(cwd, 'node_modules', '.bin', name)
    return os.path.exists(path)


def composer_exists(name):
    """
    Check whether or not a cli tool exists in vendor/bin/{name}
    relative to os.cwd

    @return boolean
    """
    cwd = os.getcwd()
    path = os.path.join(cwd, 'vendor', 'bin', name)
    return os.path.exists(path)


def go_bin_path(name):
    """
    Get the path to a go binary. Handles traversing the GOPATH

    @return str
    """
    gopath = os.environ.get('GOPATH')
    if not gopath:
        log.warn('GOPATH is not defined in environment, '
                 'cannot locate go tools')
        return ''
    for dirname in gopath.split(os.pathsep):
        if os.path.exists(os.path.join(dirname, 'bin', name)):
            return os.path.join(dirname, 'bin', name)
    return ''


def bundle_exists(name):
    """
    Check whether or not a ruby tool exists in
    the os.cwd using bundler.

    This assumes that you installed bundler packages
    into ./bundle as documented in the README.

    @return boolean
    """
    try:
        installed = subprocess.check_output(['bundle', 'list'])
    except (subprocess.CalledProcessError, FileNotFoundError, IOError):
        return False
    return name.encode() in installed
