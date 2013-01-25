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


class ChangeCollection(object):
    """
    Collection of changed files converts json
    data into more usuable data
    """

    def __init__(self, contents):
        self._changes = []
        self._index = 0
        for change in contents:
            self._add(change)

    def _add(self, content):
        change = ChangedFile(content)
        self._changes.append(change)

    def __len__(self):
        return len(self._changes)

    def __iter__(self):
        try:
            result = self._changes[self.index]
        except IndexError:
            raise StopIteration
        self._index += 1
        return result

    def next(self):
        return

    def get_files(self):
        """
        Get the names of all files that have changed
        """
        pass

    def get(self, filename):
        """
        Get all the changes that match a filename.
        """
        pass


class ChangedFile(object):
    """
    Contains all the changes for a single file.
    Changes are stored by the commit that introduced them.
    """
    def __init__(self, changes):
        pass

    def all_changes(self):
        """
        Get all the changes for a given file independant
        of which commit changed them.
        """

    def line_changed(self, line):
        """
        Find out if a particular line changed in the commits
        affecting this file.
        """

    def line_changed_on(self, line):
        """
        Get the commit(s) a line changed on
        """
