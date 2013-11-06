import logging
import time
from collections import namedtuple

log = logging.getLogger(__name__)

Comment = namedtuple('Comment', ['filename', 'line', 'position', 'body'])


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

    def publish(self, problems, head_sha, summary_threshold=None):
        """
        Publish the review.

        Existing comments are loaded, and compared
        to new problems. Once the new unique problems
        are distilled new comments are published.
        """
        log.info('Publishing review of %s to github.', self._number)

        problem_count = len(problems)
        if not problems.has_changes():
            return self.publish_empty_comment()
        if problem_count == 0:
            return self.publish_ok_comment()

        under_threshold = summary_threshold is None or problem_count < summary_threshold

        self.load_comments()
        self.remove_existing(problems)
        if under_threshold:
            self.publish_problems(problems, head_sha)
        else:
            self.publish_summary(problems)

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
                None,
                comment.body,
                int(comment.position))
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
            problems.remove(comment.filename, comment.position, comment.body)

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
                'path': error.filename,
                'position': error.position,
                'body': error.body,
            }
            log.debug("Publishing comment '%s'", comment)
            try:
                self._gh.pull_requests.comments.create(self._number, comment)
            except:
                log.warn("Failed to save comment '%s'", comment)

    def publish_ok_comment(self):
        comment = ':+1: No lint errors found.'
        self._gh.issues.comments.create(self._number, comment)

    def publish_empty_comment(self):
        msg = ('Could not review pull request. '
               'It may be too large, or contain no reviewable changes.')
        self._gh.issues.comments.create(self._number, msg)

    def publish_summary(self, problems):
        msg = "There are {0} errors:\n\n".format(len(problems))
        for problem in problems:
            msg += "* {0.filename}, line {0.line} - {0.body}\n".format(problem)

        self._gh.issues.comments.create(self._number, msg)


class Problems(object):
    """
    Collection class for holding all the problems found
    during automated review.

    Used by tool objects to collect problems, and by
    the Review objects to publish results.
    """
    _base = None

    def __init__(self, base=None, changes=None):
        self._items = []
        self._changes = changes
        if base:
            self._base = base.rstrip('/') + '/'

    def set_changes(self, changes):
        self._changes = changes

    def has_changes(self):
        return self._changes and len(self._changes) > 0

    def _trim_filename(self, filename):
        if not self._base:
            return filename
        return filename[len(self._base):]

    def line_to_position(self, filename, line):
        """
        Convert the line number in the final file to a diff offset

        Saving comments in github requires line offsets no line numbers.
        Mapping line numbers makes saving possible.
        """
        if not self._changes:
            return line
        return self._changes.line_position(filename, line)

    def all(self, filename=None):
        if filename:
            return [error for error in self._items if error[0] == filename]
        return self._items

    def add(self, filename, line, text, position=None):
        """
        Add a problem to the review.
        
        If position is not supplied the diff collection will be scanned
        and the line numbers diff offset will be fetched from there.
        """
        filename = self._trim_filename(filename)
        if not position:
            position = self.line_to_position(filename, line)
        error = Comment(
            filename=filename,
            line=line,
            position=position,
            body=text)
        if error not in self._items:
            log.debug("Adding error '%s'", error)
            self._items.append(error)

    def add_many(self, problems):
        """
        Add multiple problems to the review.
        """
        for p in problems:
            self.add(*p)

    def limit_to_changes(self):
        """
        Limit the contained problems to only those changed
        in the DiffCollection
        """
        self._items = [error for error in self._items
                       if self._changes.has_line_changed(error.filename, error.line)]

    def remove(self, filename, position, body):
        """
        Remove a problem from the list based on the filename
        position and comment.
        """
        found = False
        for i, item in enumerate(self._items):
            if item.filename == filename and item.position == position and item.body == body:
                found = i
                break
        if found is not False:
            del self._items[found]

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        i = 0
        length = len(self._items)
        while i < length:
            yield self._items[i]
            i += 1
