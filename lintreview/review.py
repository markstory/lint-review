import logging

log = logging.getLogger(__name__)


class Review(object):
    """
    Holds the comments from a review can
    add track problems logged and post new problems
    to github.
    """

    def __init__(self, gh, number, base_path=None):
        self._gh = gh
        self._problems = {}
        self._comments = {}
        self._number = number
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

    def comments(self, filename):
        return self._comments.get(filename)

    def publish(self):
        self.load_comments()
        self.filter_existing()
        self.publish_new_problems()

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

    def load_comments(self):
        """
        Load the existing comments on a pull request

        Results in a structure that is similar to the one used
        for problems
        """
        log.debug("Loading comments for pull request '%s'", self._number)
        comments = self._gh.pull_requests.comments.list(self._number).all()

        for comment in comments:
            filename = comment.path
            if not self._comments.get(filename):
                self._comments[filename] = []
            if not comment.position:
                log.debug("Ignoring outdated diff comment '%s'", comment.id)
                continue
            content = (int(comment.position), comment.body)
            self._comments[filename].append(content)

    def filter_existing(self):
        """
        Filters the problems based on existing comments.

        Remove problems that match the line + comment body of
        an existing comment. We'll assume the program put
        the comment there, and not a human.
        """
        for filename, problems in self._problems.iteritems():
            for i, error in enumerate(problems):
                if error in self._comments[filename]:
                    del self._problems[filename][i]
