import logging

log = logging.getLogger(__name__)


class Review(object):
    """
    Holds the comments from a review can
    add track problems logged and post new problems
    to github.
    """

    def __init__(self, gh, number):
        self._gh = gh
        self._comments = Problems()
        self._number = number

    def comments(self, filename):
        return self._comments.all(filename)

    def publish(self, problems, head_sha):
        """
        Publish the review.

        Existing comments are loaded, and compared
        to new problems. Once the new unique problems
        are distilled new comments are published.
        """
        log.info('Publishing review of %s to github.', self._number)

        problem_count = len(problems)
        if problem_count:
            self.load_comments()
            self.remove_existing(problems)
            self.publish_problems(problems, head_sha)
        else:
            self.publish_ok_comment()

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
            if not comment.position:
                log.debug("Ignoring outdated diff comment '%s'", comment.id)
                continue
            self._comments.add(
                filename,
                int(comment.position),
                comment.body)
        log.debug("'%s' comments loaded", len(self._comments))

    def remove_existing(self, problems):
        """
        Modifies the problems parameter removing
        problems that already have matching comments.
        Filters the problems based on existing comments.

        Remove problems that match the line + comment body of
        an existing comment. We'll assume the program put
        the comment there, and not a human.
        """
        for comment in self._comments:
            problems.remove(*comment)

    def publish_problems(self, problems, head_commit):
        """
        Publish the issues contains in the problems
        parameter. changes is used to fetch the commit sha
        for the comments on a given file.
        """
        log.debug("Publishing (%s) new comments for '%s'",
                  len(problems), self._number)
        for error in problems:
            comment = {
                'commit_id': head_commit,
                'path': error[0],
                'position': error[1],
                'body': error[2],
            }
            log.debug("Publishing comment '%s'", comment)
            try:
                self._gh.pull_requests.comments.create(self._number, comment)
            except:
                log.warn("Failed to save comment '%s'", comment)

    def publish_ok_comment(self):
        comment = {
            'body': ':+1: No lint errors found.'
        }
        self._gh.issues.comments.create(self._number, comment)


class Problems(object):
    """
    Collection class for holding all the problems found
    during automated review.

    Used by tool objects to collect problems, and by
    the Review objects to publish results.
    """
    _base = None

    def __init__(self, base=None):
        self._items = []
        if base:
            self._base = base.rstrip('/') + '/'

    def _trim_filename(self, filename):
        if not self._base:
            return filename
        return filename[len(self._base):]

    def all(self, filename=None):
        if filename:
            return [error for error in self._items if error[0] == filename]
        return self._items

    def add(self, filename, line, text):
        """
        Add a problem to the review.
        """
        filename = self._trim_filename(filename)
        error = (filename, line, text)
        if error not in self._items:
            log.debug("Adding error '%s'", error)
            self._items.append(error)

    def add_many(self, problems):
        """
        Add multiple problems to the review.
        """
        for p in problems:
            self.add(*p)

    def limit_to(self, changes):
        """
        Limit the contained problems to only those changed
        in the DiffCollection
        """
        self._items = [error for error in self._items
                       if changes.has_line_changed(error[0], error[1])]

    def remove(self, filename, line, comment):
        """
        Remove a problem from the list based on the filename
        line and comment.
        """
        kill = (filename, line, comment)
        try:
            index = self._items.index(kill)
            del self._items[index]
        except:
            pass

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        i = 0
        length = len(self._items)
        while i < length:
            yield self._items[i]
            i += 1
