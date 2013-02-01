import logging
import re

log = logging.getLogger(__name__)


class Review(object):
    """
    Holds the comments from a review can
    add track problems logged and post new problems
    to github.
    """

    def __init__(self, gh, base_path=None):
        self._gh = gh
        self._problems = {}
        self._base = base_path

    def _trim_filename(self, filename):
        if not self._base:
            return filename
        return filename[len(self._base):]

    def add_problems(self, filename, problems):
        """
        Add multiple problems to the review.
        """
        for p in problems:
            self.add_problem(filename, p)

    def add_problem(self, filename, problem):
        """
        Add a problem to the review.
        """
        filename = self._trim_filename(filename)
        if not self._problems.get(filename):
            self._problems[filename] = []
        self._problems[filename].append(problem)

    def problems(self, filename):
        return self._problems.get(filename)

    def publish():
        pass


class DiffCollection(object):
    """
    Collection of changes made in a pull request.
    Converts json data into more usuable objects.
    """

    def __init__(self, contents):
        self._changes = []
        self._index = 0
        for change in contents:
            self._add(change)

    def _add(self, content):
        change = Diff(content)
        self._changes.append(change)

    def __len__(self):
        return len(self._changes)

    def __iter__(self):
        return self

    def next(self):
        try:
            result = self._changes[self._index]
        except IndexError:
            raise StopIteration
        self._index += 1
        return result

    def get_files(self):
        """
        Get the names of all files that have changed
        """
        return [change.filename for change in self._changes]

    def all_changes(self, filename):
        """
        Get all the changes for a given file independant
        of which commit changed them.
        """
        return [change for change in self._changes
                if change.filename == filename]

    def has_line_changed(self, filename, line):
        """
        Check whether or not a line has changed in
        a file.

        Useful for verifying that errors from tools
        are new and likely to be related to the lines
        changed in the pull request.
        """
        changed = [change for change in self.all_changes(filename)
                   if change.has_line_changed(line)]
        return len(changed) > 0


class Diff(object):
    """
    Contains the changes for a single file.
    Github's API returns one Diff per file
    in a pull request.
    """
    def __init__(self, data):
        self._data = data
        self._parse_diff(data['patch'])

    def _parse_diff(self, patch):
        """
        Parses the diff data and stores the list of
        line numbers that were added in this diff.

        We don't care about deletions as they won't
        have lint errors in them.
        """
        hunk_pattern = re.compile('\@\@ \-\d+,\d+ \+(\d+),\d+ \@\@')

        line_num = 1
        additions = []
        lines = patch.split("\n")
        for line in lines:
            # Set the line_num at the start of the hunk
            match = hunk_pattern.match(line)
            if match:
                line_num = int(match.group(1)) - 1
                continue
            # Increment lines through additions and
            # unchanged lines.
            if not line.startswith('-'):
                line_num += 1
            if line.startswith('+'):
                additions.append(line_num)
        self._additions = set(additions)

    @property
    def filename(self):
        return self._data['filename']

    @property
    def commit(self):
        return self._data['sha']

    def has_line_changed(self, line):
        """
        Find out if a particular line changed in this commit's
        diffs
        """
        return line in self._additions
