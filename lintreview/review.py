import logging

log = logging.getLogger(__name__)


class IssueComment(object):
    """
    A simple comment that will be published as a
    pull request/issue comment.
    """
    filename = None
    line = 0
    position = 0
    body = None

    def __init__(self, body=''):
        self.body = body

    def publish(self, gh, pull_request_number, head_commit=None):
        log.debug("Publishing issue comment '%s'", self.body)
        try:
            gh.issue(pull_request_number).create_comment(self.body)
        except:
            log.warn("Failed to save comment '%s'", self.body)

    def __eq__(self, other):
        """
        Overload eq to make testing much simpler.
        """
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return "%s(filename=%s, line=%s, position=%s, body=%s)" % (
            str(self.__class__),
            self.filename,
            self.line,
            self.position,
            self.body)


class IssueLabel(object):

    def __init__(self, label):
        self.label = label

    def remove(self, gh, pull_request_number):
        try:
            issue = gh.issue(pull_request_number)
            labels = issue.labels()
            if not any(self.label == label.name for label in labels):
                return
            log.debug("Removing issue label '%s'", self.label)
            issue.remove_label(self.label)
        except:
            log.warn("Failed to remove label '%s'", self.label)

    def publish(self, gh, pull_request_number):
        # remove+add to show latest activity
        self.remove(gh, pull_request_number)
        log.debug("Publishing issue label '%s'", self.label)
        try:
            # create label if it doesn't exist yet
            if not gh.label(self.label):
                gh.create_label(
                    name=self.label,
                    color="bfe5bf",  # a nice light green
                )
            gh.issue(pull_request_number).add_labels(self.label)
        except:
            log.warn("Failed to add label '%s'", self.label)


class Comment(IssueComment):
    """A line comment on the pull request."""

    def __init__(self, filename='', line=0, position=0, body=''):
        super(Comment, self).__init__(body)
        self.line = line
        self.filename = filename
        self.position = position

    def publish(self, gh, pull_request_number, head_commit):
        comment = {
            'commit_id': head_commit,
            'path': self.filename,
            'position': self.position,
            'body': self.body,
        }
        log.debug("Publishing line comment '%s'", comment)
        try:
            gh.pull_request(pull_request_number) \
                .create_review_comment(**comment)
        except:
            log.warn("Failed to save comment '%s'", comment)


class Review(object):
    """
    Holds the comments from a review can
    add track problems logged and post new problems
    to github.
    """

    def __init__(self, gh, number, config=None):
        config = config if config else {}
        self._gh = gh
        self._comments = Problems()
        self._number = number
        self._pr = self._gh.pull_request(self._number)
        self.config = config

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

        if not problems.has_changes():
            return self.publish_empty_comment()

        self.load_comments()
        self.remove_existing(problems)

        problem_count = len(problems)
        under_threshold = (summary_threshold is None or
                           problem_count < summary_threshold)

        if under_threshold:
            self.publish_problems(problems, head_sha)
        else:
            self.publish_summary(problems)
        self.publish_status(problem_count)

    def load_comments(self):
        """
        Load the existing comments on a pull request

        Results in a structure that is similar to the one used
        for problems
        """
        log.debug("Loading comments for pull request '%s'", self._number)
        comments = list(self._pr.review_comments())

        for comment in comments:
            # Workaround github3 not exposing attributes for what we need.
            guts = comment.as_dict()
            filename = guts['path']
            if not guts['position']:
                log.debug("Ignoring outdated diff comment '%s'", comment.id)
                continue
            self._comments.add(
                filename,
                None,
                comment.body,
                int(guts['position']))
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
        self.remove_ok_label()
        for error in problems:
            error.publish(self._gh, self._number, head_commit)

    def publish_status(self, problem_count):
        """
        Update the build status for the tip commit.
        The build will be a success if there are 0 problems.
        """
        state = 'failure'
        description = 'Lint errors found, see pull request comments.'
        if problem_count == 0:
            self.publish_ok_label()
            self.publish_ok_comment()
            state = 'success'
            description = 'No lint errors found.'
        self._gh.create_status(
            self._pr.head.sha,
            state,
            None,
            description,
            self.config.get('APP_NAME', 'lintreview'))

    def remove_ok_label(self):
        label = self.config.get('OK_LABEL', False)
        if label:
            IssueLabel(label).remove(self._gh, self._number)

    def publish_ok_label(self):
        """
        Optionally publish the OK_LABEL if it is enabled.
        """
        label = self.config.get('OK_LABEL', False)
        if label:
            issue_label = IssueLabel(label)
            issue_label.publish(self._gh, self._number)

    def publish_ok_comment(self):
        """
        Optionally publish the OK_COMMENT if it is enabled.
        """
        comment = self.config.get('OK_COMMENT', False)
        if comment:
            comment = IssueComment(comment)
            comment.publish(self._gh, self._number)

    def publish_empty_comment(self):
        self.remove_ok_label()
        body = ('Could not review pull request. '
                'It may be too large, or contain no reviewable changes.')
        comment = IssueComment(body)
        comment.publish(self._gh, self._number)

    def publish_summary(self, problems):
        self.remove_ok_label()
        body = "There are {0} errors:\n\n".format(len(problems))
        for problem in problems:
            body += "* {0.filename}, line {0.line} - {0.body}\n".format(
                problem)
        comment = IssueComment(body)
        comment.publish(self._gh, self._number)


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
            return [error
                    for error in self._items
                    if error.filename == filename]
        return self._items

    def add(self, filename, line=None, body=None, position=None):
        """
        Add a problem to the review.

        If position is not supplied the diff collection will be scanned
        and the line numbers diff offset will be fetched from there.
        """
        if isinstance(filename, IssueComment):
            self._items.append(filename)
            return

        filename = self._trim_filename(filename)
        if not position:
            position = self.line_to_position(filename, line)
        error = Comment(
            filename=filename,
            line=line,
            position=position,
            body=body)
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
        changes = self._changes

        def sieve(err):
            if err.filename is None:
                return True
            if changes.has_line_changed(err.filename, err.line):
                return True
            return False
        self._items = [error for error in self._items if sieve(error)]

    def remove(self, filename, position, body):
        """
        Remove a problem from the list based on the filename
        position and comment.
        """
        found = False
        for i, item in enumerate(self._items):
            if (item.filename == filename and
                    item.position == position and item.body == body):
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
