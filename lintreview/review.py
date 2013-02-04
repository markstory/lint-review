import logging

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

    def filter_problems(self, changes):
        """
        Filter the problems stored internally to
        only those in the lines changed inside the DiffCollection
        provided.
        """
        for filename, problems in self._problems.iteritems():
            for i, error in enumerate(problems):
                if not changes.has_line_changed(filename, error[0]):
                    del self._problems[filename][i]
