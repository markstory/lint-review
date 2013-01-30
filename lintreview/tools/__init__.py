import logging
import os
import subprocess

log = logging.getLogger(__name__)


class Tool(object):
    """
    Base class for tools
    """
    name = ''
    options = []

    def __init__(self, review, options=None):
        self.review = review
        self.options = options

    def check_dependencies(self):
        """
        Used to check for a tools commandline
        executable or other dependencies.
        """
        return True

    def execute(self, files):
        """
        Execute the tool against the files in a
        pull request. Files will be filtered by
        match_file()
        """
        log.info('Running %s', self.name)
        matching_files = []
        for f in files:
            if self.match_file(f):
                matching_files.append(f)
        self.process_files(matching_files)
        self.post_process(files)

    def match_file(self, filename):
        """
        Used to check if files can be handled by this
        tool. Often this will just file extension checks.
        """
        return True

    def process_files(self, files):
        """
        Used to process all files. Can be overridden by tools
        that support linting more than one file at a time.
        """
        log.debug('Processing %s files with %s', files, self.name)
        for f in files:
            problems = self.process(f)
            if problems:
                self.review.add_problems(f, problems)

    def process(self, filename):
        """
        Process a single file, and collect
        tool output for each file
        """
        return False

    def post_process(self, files):
        """
        Do any post processing required by
        a tool.
        """
        return False


def run_command(
        command,
        split=False,
        ignore_error=False,
        include_errors=True):
    """
    Execute subprocesses.
    """
    log.debug('Running %s', command)
    env = os.environ.copy()
    if include_errors:
        error_pipe = subprocess.STDOUT
    else:
        error_pipe = subprocess.PIPE
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=error_pipe,
        shell=False,
        universal_newlines=True,
        env=env)
    if split:
        data = process.stdout.readlines()
    else:
        data = process.stdout.read()
    return_code = process.wait()
    if return_code and not ignore_error:
        raise Exception('Failed to execute %s', command)
    return data
