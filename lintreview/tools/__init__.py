import logging
import os
import re
import collections

import lintreview.docker as docker

from lintreview.review import IssueComment
from xml.etree import ElementTree

log = logging.getLogger(__name__)
buildlog = logging.getLogger('buildlog')

version_re = re.compile(r'([\d]+[\d.a-z]+)')


def extract_version(text):
    """
    Extract the first matching version number from text.
    """
    match = version_re.search(text)
    if match:
        return match.group(1)
    return ''


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

    @property
    def version(self):
        """
        Get the version number for the tool. Implementations
        should consider using functools.cached_property to
        avoid wasting time.
        """
        return ''

    def execute(self, files):
        """
        Execute the tool against the files in a
        pull request. Files will be filtered by
        match_file()
        """
        matching_files = [f for f in files if self.match_file(f)]
        num_files = len(matching_files)

        if not num_files:
            log.debug('No matching files for %s', self.name)
            return

        buildlog.info('Running %s on %d files', self.name, num_files)
        log.debug('Processing %s files with %s', matching_files, self.name)
        try:
            self.process_files(matching_files)
        except docker.TimeoutError:
            msg = 'Failed to run %s linter. It timed out during execution.'
            self.problems.add(IssueComment(msg % (self.name)))

    def execute_commits(self, commits):
        """
        Hook method for looking at commits.

        This is useful for tools that need to look at
        commit comments or other parts of individual commits.

        Tools implementing this method can expect a list of
        commit objects from the github API.
        """
        pass

    def execute_fixer(self, files):
        """
        Execute the fixer on all of the provided files.

        Files will be filtered by match_file() before applying
        the fixer.
        """
        matching_files = [f for f in files if self.match_file(f)]
        num_files = len(matching_files)
        if not num_files:
            return
        buildlog.info('Running fixer %s on %d files', self.name, num_files)
        self.process_fixer(matching_files)

    def has_fixer(self):
        """
        Hook method to check if a fixer exists and should be run.

        For tools that have fixers, and the configuration file has
        enabled fixers for that tool, this method should return True.
        """
        return False

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

    def process_fixer(self, files):
        """
        Used to process fixers. Overridden by tools.
        """
        return False

    def _relativize_filename(self, files, name):
        """
        Some tools convert filenames to absolute paths.
        Convert each of the files in `files` to an
        absolute path to locate the filename
        """
        if name in files:
            # was already relative to repository
            return name

        abs_name = os.path.realpath(name)
        for f in files:
            abs_path = os.path.realpath(f)

            # output filename was absolute
            if abs_path == name:
                return f

            # output filename is relative to base_path
            if self.base_path and os.path.join(self.base_path, f) == abs_name:
                return f

        msg = "Could not locate '%s' in changed files: %s." % (name, files)
        raise ValueError(msg)

    def apply_base(self, value):
        """
        Used to convert config values into absolute paths.

        If the tool has a base_path set, the value will be relative to
        that base path. If the value traverses to an ancestor of the base_path
        only the basename of value will be returned. This is to prevent
        directory traversal outside of the basedir.
        """
        if not self.base_path:
            return value
        path = os.path.abspath(os.path.join(self.base_path, value))
        if path.startswith(self.base_path):
            return path
        return os.path.basename(value)

    def __repr__(self):
        return '<%sTool config: %s>' % (self.name, self.options)


def factory(config, problems, base_path):
    """
    Consumes a lintreview.config.ReviewConfig object
    and creates a list of linting tools based on it.
    """
    log.debug('Generating tool list from repository configuration')
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
        except ImportError:
            log.info('Could not import linter `%s`', linter)
            raise ImportError(u'Could not load linter named `{}`'.format(linter))
        except Exception:
            raise
    return tools


def run(lint_tools, files, commits):
    """
    Create and run tools.

    Uses the ReviewConfig, problemset, and list of files to iteratively
    run each tool across the various files in a pull request.

    file paths are converted into docker paths as all
    tools run in docker containers.
    """
    files = [docker.apply_base(f) for f in files]

    log.info('Running for %d files', len(files))
    for tool in lint_tools:
        previous_total = len(tool.problems)
        if tool.version:
            buildlog.info('%s version is: %s', tool.name, tool.version)
        tool.execute(files)
        tool.execute_commits(commits)
        buildlog.info('%s added %s review notes', tool.name, len(tool.problems) - previous_total)


def process_quickfix(problems, output, filename_converter, columns=3):
    """
    Process vim quickfix style results.

    Each element in `output` should be formatted like::

        <filename>:<line>:<col>:[ ]<message>

    The `columns` parameter can be used to parse quickfix
    output that contains start/end column numbers allowing formats
    like:

        <filename>:<line>:<start>:<end>[ ]<message>

    to be parsed.
    """
    for line in output:
        parts = line.split(':', columns)
        if len(parts) < columns:
            continue
        message = parts[-1].strip()
        try:
            lineno = int(parts[1])
        except ValueError:
            log.info("Error parsing quickfix output. Dropping message=%s", line)
            continue
        filename = filename_converter(parts[0].strip())
        problems.add(filename, lineno, message)


def _parse_xml(xml):
    if not xml:
        # Some tools return "" if no errors are found
        return
    try:
        return ElementTree.fromstring(xml)
    except Exception:
        if len(xml) > 8192:
            head = xml[0:250].encode('utf-8')
            tail = xml[-250:].encode('utf-8')
            log.error("Unable to parse XML head=%s, tail=%s", head, tail)
        else:
            log.error('Unable to parse XML %s', xml.encode('utf-8'))
        raise


def process_checkstyle(problems, xml, filename_converter):
    """
    Process a checkstyle XML file.

    If the output is not XML or is malformed XML an error will be raised.
    """
    tree = _parse_xml(xml)
    if tree is None or len(tree) == 0:
        return
    for f in tree.findall('file'):
        filename = f.get('name')
        if filename_converter:
            filename = filename_converter(filename)
        for err in f.findall('error'):
            line = err.get('line')
            message = err.get('message')
            try:
                lines = []
                if line in ('undefined', 'null'):
                    lines = [0]
                if ',' in line:
                    lines = [int(x) for x in line.split(',')]
                else:
                    lines = [int(line)]
            except Exception as e:
                log.info(
                    "Error parsing checkstyle output. "
                    "Dropping message=%s line=%s"
                    "Error was %s", message, line, e)
            for line in lines:
                problems.add(filename, line, message)


def process_pmd(problems, xml, filename_converter):
    """Process a PMD XML file.
    """
    tree = _parse_xml(xml)
    if len(tree) == 0:
        return
    for f in tree.findall('file'):
        filename = f.get('name')
        if filename_converter:
            filename = filename_converter(filename)
        for err in f.findall('violation'):
            try:
                line = int(err.get('beginline') or err.get('endline'))
                message_parts = [
                    '%s:' % err.get('rule') if err.get('rule') else None,
                    err.text.strip(),
                    'See: %s' % err.get('externalInfoUrl') if err.get('externalInfoUrl') else None,
                ]
                message = ' '.join(filter(None, message_parts))
                problems.add(filename, line, message)
            except Exception:
                log.info(
                    'Could not parse pmd output. '
                    'Dropping violation=%s',
                    ElementTree.tostring(err))


def stringify(value):
    """
    PHPCS uses a , separated strings in many places
    because of how it handles options we have to do bad things
    with string concatenation.
    """
    if isinstance(value, str):
        return value
    if isinstance(value, collections.Iterable):
        return ','.join(value)
    return str(value)


def commalist(value):
    """
    Convert a comma separated string into a list
    If ``value`` is already a list or tuple it will
    be returned.
    """
    if isinstance(value, str):
        return [v.strip() for v in value.split(',')]
    if isinstance(value, (set, list)):
        return value


def python_image(config):
    supported = {
        '3': 'python3',
        '2': 'python2'
    }
    if not config:
        return supported['2']
    if 'python' not in config:
        return supported['2']
    version = str(config['python'])
    if version not in supported:
        return supported['2']
    return supported[version]
