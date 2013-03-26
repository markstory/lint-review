import os


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
