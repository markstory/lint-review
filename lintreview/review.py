import logging

log = logging.getLogger(__name__)


class CodeReview(object):
    """
    Knows how to run a code review.
    Uses the config, github and pull request information
    to run the required tools and post comments on problems.
    """

    def __init__(self, config, gh, pull_request):
        self._config = config
        self._gh = gh
        self._pull_request = pull_request

    def run():
        """
        Run the review for a pull request.
        """


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


class Diff(object):
    """
    Contains the changes for a single file,
    from a single commit.
    """
    def __init__(self, data):
        self._data = data

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
