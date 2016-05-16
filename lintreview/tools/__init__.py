import logging
import os
import subprocess
from xml.etree import ElementTree

log = logging.getLogger(__name__)


class Tool(object):
    """
    Base class for tools
    """
    name = ''

    def __init__(self, problems, options=None, base_path=None):
        self.problems = problems
        self.base_path = base_path
        self.options = {}
        if isinstance(options, dict):
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
        matching_files = []
        for f in files:
            if self.match_file(f):
                matching_files.append(f)
        if len(matching_files):
            log.info('Running %s for %s', self.name, matching_files)
            self.process_files(matching_files)
            self.post_process(files)
        else:
            log.debug('No matching files for %s', self.name)

    def execute_commits(self, commits):
        """
        Hook method for looking at commits.

        This is useful for tools that need to look at
        commit comments or other parts of individual commits.

        Tools implementing this method can expect a list of
        commit objects from the github API.
        """
        pass

    def match_file(self, filename):
        """
        Used to check if files can be handled by this
        tool. Often this will just file extension checks.
        """
        return True

    def process_files(self, files):
        """
        Used to process all files. Overridden by tools
        """
        return False

    def post_process(self, files):
        """
        Do any post processing required by
        a tool.
        """
        return False

    def _relativize_filename(self, files, name):
        """
        Some tools convert filenames to absolute paths.
        Convert each of the files in `files` to an
        absolute path to locate the filename
        """
        if name in files:
            return name  # looks like it was already relative

        for f in files:
            abs_path = os.path.realpath(f)
            if abs_path == name:
                return f
        msg = "Could not locate '%s' in changed files." % (name, )
        raise ValueError(msg)

    def _process_checkstyle(self, xml, filename_converter=None):
        """
        Process a checkstyle xml file.

        Errors and warnings in the XML file will
        be added to the problems object.
        """
        if not xml:
            # Some tools return "" if no errors are found
            return
        try:
            tree = ElementTree.fromstring(xml)
        except:
            log.debug('Checkstyle XML - %s', xml)
            log.error("Unable to parse checkstyleXML from %s.", self.name)
            raise

        for f in tree.findall('file'):
            filename = f.get('name')
            if filename_converter:
                filename = filename_converter(filename)
            for err in f.findall('error'):
                line = err.get('line')
                message = err.get('message')
                if ',' in line:
                    lines = [int(x) for x in line.split(',')]
                else:
                    lines = [int(line)]
                add = lambda x: self.problems.add(filename, x, message)
                map(add, lines)

    def apply_base(self, value):
        """
        Used to convert config values into absolute paths. If `value`
        does not have a os.sep it will be returned unaltered.
        """
        if os.sep not in value:
            return value
        if not self.base_path:
            return value
        return os.path.join(self.base_path, value)

    def __repr__(self):
        return '<%sTool config: %s>' % (self.name, self.options)


def run_command(
        command,
        split=False,
        ignore_error=False,
        include_errors=True,
        shell=False,
        cwd=None):
    """
    Execute subprocesses.
    """
    log.info('Running %s', ' '.join(command))

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
        shell=shell,
        universal_newlines=True,
        env=env,
        cwd=cwd)
    if split:
        data = process.stdout.readlines()
    else:
        data = process.stdout.read()
    return_code = process.wait()
    if return_code and not ignore_error:
        raise Exception('Failed to execute %s', command)
    return data


def factory(problems, config, base_path):
    """
    Consumes a lintreview.config.ReviewConfig object
    and creates a list of linting tools based on it.
    """
    tools = []
    for linter in config.linters():
        linter_config = config.linter_config(linter)
        try:
            classname = linter.capitalize()
            log.debug("Attempting to import 'lintreview.tools.%s'", linter)
            mod = __import__('lintreview.tools.' + linter, fromlist='*')
            clazz = getattr(mod, classname)
            tool = clazz(problems, linter_config, base_path)
            tools.append(tool)
        except:
            log.error("Unable to import tool '%s'", linter)
            raise
    return tools


def run(config, problems, files, commits, base_path):
    """
    Create and run tools.

    Uses the ReviewConfig, problemset, and list of files to iteratively
    run each tool across the various files in a pull request.
    """
    log.debug('Generating tool list from repository configuration')
    lint_tools = factory(problems, config, base_path)

    log.info('Running lint tools on %s', files)
    for tool in lint_tools:
        log.debug('Runnning %s', tool)
        tool.execute(files)
        tool.execute_commits(commits)
