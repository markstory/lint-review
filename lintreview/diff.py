from __future__ import absolute_import
import fnmatch
import re
import logging
from collections import namedtuple

log = logging.getLogger(__name__)

# Adapter to make parsed text diffs quack like github API
# responses.
DiffAdapter = namedtuple(
    'DiffAdapter',
    ('patch', 'filename', 'sha', 'status',
     'additions', 'deletions', 'changes')
)


def parse_diff(text):
    """Parse the output of `git diff` into
    a DiffCollection and set of diff objects
    """
    if not text:
        raise ParseError('No diff provided')
    file_pattern = r'diff \-\-git a/.* b/.*'
    blocks = re.split(file_pattern, text)
    diffs = []
    for chunk in blocks:
        if len(chunk) == 0:
            continue
        diffs.append(parse_file_diff(chunk))
    if not diffs:
        msg = u'Could not parse any diffs from provided diff text.'
        raise ParseError(msg)

    return DiffCollection(diffs)


def parse_file_diff(chunk):
    filename = None
    patch = []
    for line in chunk.split('\n'):
        # Ignore the - filename and index refspec
        if line.startswith('---') or line.startswith('index'):
            continue
        if line.startswith('+++'):
            filename = line[6:]
            continue
        if not filename:
            continue
        patch.append(line)

    if not patch:
        msg = u'Could not parse diff for {}'.format(filename)
        raise ParseError(msg)

    return DiffAdapter(
        patch='\n'.join(patch),
        filename=filename,
        sha=None,
        status='modified',
        # Placeholder values to quack like github data.
        additions=1,
        deletions=1,
        changes=1)


class ParseError(RuntimeError):
    pass


class DiffCollection(object):
    """
    Collection of changes made in a pull request.
    Converts json data into more usuable objects.
    """

    def __init__(self, contents):
        self._diffs = []
        for change in contents:
            self._add(change)

    def _add(self, content):
        try:
            self._add_diff(content)
        except Exception as e:
            log.warn('Could not process diff %s. content=%s error=%s',
                     str(content),
                     content.patch,
                     e.message)

    def _add_diff(self, content):
        if not self._has_additions(content):
            log.debug('Skipping %s as it has no additions', content.filename)
            return
        change = Diff(content.patch,
                      content.filename,
                      content.sha)
        self._diffs.append(change)

    def _has_additions(self, content):
        """
        Rough check at whether or not a file diff is going
        to have additions at all.

        - Removed files never need to be linted as they are dead.
        - Renamed files don't need to be linted as they have no diff
        - Any other file with a `+` in it should be checked.
        """
        if content.status in ('removed', 'renamed'):
            return False
        if content.additions == 0 and content.deletions == 0 \
                and content.changes == 0:
            return False
        if not hasattr(content, 'patch'):
            return False
        if content.patch is None:
            return False
        return '+' in content.patch

    def __len__(self):
        return len(self._diffs)

    def __getitem__(self, index):
        return self._diffs[index]

    def __iter__(self):
        i = 0
        length = len(self._diffs)
        while i < length:
            yield self._diffs[i]
            i += 1

    def get_files(self, ignore_patterns=None):
        """Get the names of all files that have changed
        """
        return [change.filename
                for change in self._diffs
                if not self._ignore_file(change.filename, ignore_patterns)]

    def _ignore_file(self, filename, ignore_patterns):
        if not ignore_patterns:
            return False
        matches = [fnmatch.fnmatch(filename, pattern)
                   for pattern in ignore_patterns]
        return any(matches)

    def all_changes(self, filename):
        """Get all the changes for a given file independant
        of which commit changed them.
        """
        return [change for change in self._diffs
                if change.filename == filename]

    def has_line_changed(self, filename, line):
        """Check whether or not a line has changed in a file.

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
    """Contains the changes for a single file.

    Github's API returns one Diff per file
    in a pull request.
    """
    def __init__(self, patch, filename, sha, hunks=None):
        self._filename = filename
        self._sha = sha
        if hunks is not None:
            for hunk in hunks:
                assert isinstance(hunk, Hunk), 'Hunk objects are required.'
            self._hunks = tuple(hunks)
        else:
            self._parse_hunks(patch)

    def _parse_hunks(self, patch):
        """Parse the diff data into a collection of hunks.

        We track the 'new' version of the diff, and not the old
        version as we care about the new state of the file when
        applying linters. When applying fixers if an added/modified
        line intersects with the previous change we also care.
        """
        hunks = []
        hunk_separator = r'(^\@\@ \-\d+,\d+ \+\d+(?:,\d+)? \@\@.*?\n)'
        blocks = re.split(hunk_separator, patch, 0, re.M)

        if len(blocks) and blocks[0] == '':
            del blocks[0]

        offset = 0
        header = body = False
        for block in blocks:
            if block.startswith('@@'):
                header = block
            else:
                body = block
            if header and body:
                hunks.append(Hunk(header, body, offset))
                offset += 1 + body.count('\n')
                header = body = False
        self._hunks = tuple(hunks)

    @property
    def hunks(self):
        return self._hunks

    @property
    def filename(self):
        return self._filename

    @property
    def patch(self):
        return "".join([hunk.patch for hunk in self._hunks])

    @property
    def commit(self):
        return self._sha

    def as_diff(self):
        """Convert this Diff object into a string
        that can be used with git apply. The generated diff
        will be lacking the `index` line as this object doesn't track
        enough state to preserve that data because it is missing in some
        of the sources we interact with.
        """
        header = u"""diff --git a/{filename} b/{filename}
--- a/{filename}
+++ b/{filename}
"""
        header = header.format(filename=self.filename)
        return header + self.patch

    def has_line_changed(self, line):
        """
        Find out if a particular line changed in this commit's
        diffs
        """
        for hunk in self._hunks:
            if hunk.has_line_changed(line):
                return True
        return False

    def added_lines(self):
        """Get the line numbers of lines that were added"""
        adds = set()
        for hunk in self._hunks:
            adds = adds.union(hunk.added_lines())
        return adds

    def deleted_lines(self):
        """Get the line numbers of lines that were deleted"""
        dels = set()
        for hunk in self._hunks:
            dels = dels.union(hunk.deleted_lines())
        return dels

    def line_position(self, lineno):
        """
        Find the line number position given a line number in the new
        file content.
        """
        for hunk in self._hunks:
            position = hunk.line_position(lineno)
            if position:
                return position
        return None

    def intersection(self, other):
        """Get the intersecting or overlapping hunks that
        intersect with hunks in `other`"""
        overlapping = []
        other_added = other.added_lines()
        for hunk in self._hunks:
            added = hunk.added_lines()
            deleted = hunk.deleted_lines()
            if other_added.intersection(added) or \
                    other_added.intersection(deleted):
                overlapping.append(hunk)
        return overlapping


class Hunk(object):
    """Provide an interface for interacting with diff hunks

    Each Diff is made of multiple hunks of various sizes.
    Each Hunk begins with the ``@@`` delimiter.
    """
    start_line_pattern = re.compile('\@\@ \-(\d+),\d+ \+(\d+)(?:,\d+)? \@\@')

    def __init__(self, header, patch, offset):
        self._header = header
        self._patch = patch
        self._parse(patch, offset)

    def _parse(self, patch, offset):
        match = self.start_line_pattern.match(self._header)
        if not match:
            msg = u'Could not parse hunk header {}'.format(self._header)
            raise ParseError(msg)

        # Account for the header
        offset += 1

        # Compensate for the increment done in the line loop
        line_num = int(match.group(2)) - 1
        old_line_num = int(match.group(1)) - 1

        additions = []
        deletions = []
        line_map = {}
        for line in self._patch.split('\n'):
            # Increment lines through additions and
            # unchanged lines.
            if not line.startswith('-'):
                line_num += 1
                old_line_num += 1
            if line.startswith('-'):
                deletions.append(old_line_num + 1)
            if line.startswith('+'):
                additions.append(line_num)
                line_map[line_num] = offset
            offset += 1
        self._additions = set(additions)
        self._deletions = set(deletions)
        self._positions = line_map

    @property
    def patch(self):
        return "".join([self._header, self._patch])

    def contains_line(self, lineno):
        """Check if a hunk contains the provided lineno
        in either its deletions or additions"""
        return lineno in self._additions or lineno in self._deletions

    def has_line_changed(self, lineno):
        """Check if a line was added"""
        return lineno in self._additions

    def added_lines(self):
        """Get the lines added in this hunk"""
        return self._additions

    def deleted_lines(self):
        """Get the lines deleted in this hunk"""
        return self._deletions

    def line_position(self, line_number):
        """Find the line position given a line number in the
        new file content.

        The line position is used to post github comments.
        """
        if line_number in self._positions:
            return self._positions[line_number]
        return None
