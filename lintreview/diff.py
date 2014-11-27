import fnmatch
import re
import os
import logging

log = logging.getLogger(__name__)


class DiffCollection(object):
    """
    Collection of changes made in a pull request.
    Converts json data into more usuable objects.
    """

    def __init__(self, contents):
        self._changes = []
        for change in contents:
            self._add(change)

    def _add(self, content):
        try:
            self._add_diff(content)
        except:
            log.warn('Could not process diff %s', str(content))

    def _add_diff(self, content):
        if not self._has_additions(content):
            log.debug('Skipping %s as it has no additions', content.filename)
            return
        change = Diff(content)
        self._changes.append(change)

    def _has_additions(self, content):
        """
        Rough check at whether or not a file diff is going
        to have additions at all.

        - Removed files never need to be linted as they are dead.
        - Any other file with a `+` in it should be checked.
        """
        if content.status == 'removed':
            return False
        if not hasattr(content, 'patch'):
            return False
        return '+' in content.patch

    def __len__(self):
        return len(self._changes)

    def __iter__(self):
        i = 0
        length = len(self._changes)
        while i < length:
            yield self._changes[i]
            i += 1

    def get_files(self, append_base='', ignore_patterns=None):
        """
        Get the names of all files that have changed
        """
        if append_base:
            append_base = os.path.realpath(append_base) + os.sep
        return [append_base + change.filename
                for change in self._changes
                if not self._ignore_file(change.filename, ignore_patterns)]

    def _ignore_file(self, filename, ignore_patterns):
        if not ignore_patterns:
            return False
        matches = [fnmatch.fnmatch(filename, pattern)
                   for pattern in ignore_patterns]
        return any(matches)

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

    def line_position(self, filename, line):
        """
        Find the line position for a given file + line
        """
        changes = self.all_changes(filename)
        if len(changes):
            return changes[0].line_position(line)
        return None


class Diff(object):
    """
    Contains the changes for a single file.
    Github's API returns one Diff per file
    in a pull request.
    """
    def __init__(self, data):
        self._data = data
        self._parse_diff(data.patch)

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
        line_map = {}
        lines = patch.split("\n")
        for i, line in enumerate(lines):
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
                line_map[line_num] = i
        self._additions = set(additions)
        self._indexes = line_map

    @property
    def filename(self):
        return self._data.filename

    @property
    def commit(self):
        return self._data.sha

    def has_line_changed(self, line):
        """
        Find out if a particular line changed in this commit's
        diffs
        """
        return line in self._additions

    def line_position(self, line_number):
        """
        Find the line number position given a line number in the new
        file content.
        """
        if line_number in self._indexes:
            return self._indexes[line_number]
        return None
