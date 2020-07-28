from collections import OrderedDict
from datetime import datetime
import logging

LEVEL_INFO = 'info'
LEVEL_ERROR = 'error'

log = logging.getLogger(__name__)
buildlog = logging.getLogger('buildlog')


class IssueLabel(object):

    def __init__(self, label):
        self.label = label

    def remove(self, pull_request):
        try:
            pull_request.remove_label(self.label)
        except Exception:
            log.warn("Failed to remove label '%s'", self.label)

    def publish(self, repo, pull_request):
        self.remove(pull_request)
        log.debug("Publishing issue label '%s'", self.label)
        try:
            repo.ensure_label(self.label)
            pull_request.add_label(self.label)
        except Exception:
            log.warn("Failed to add label '%s'", self.label)


class BaseComment(object):
    """Shared behavior across comment types
    """
    level = LEVEL_ERROR
    body = ''

    def key(self):
        """Define the identifying tuple for a comment.
        This should be a tuple of the file/line of the comment.
        """
        raise NotImplementedError()

    def __eq__(self, other):
        return False

    def append_body(self, text):
        if text not in self.body:
            self.body += "\n" + text

    def summary_text(self):
        return self.body


class IssueComment(BaseComment):
    """A simple comment that will be published as a
    pull request/issue comment.
    """

    def __init__(self, body=''):
        self.body = body

    def key(self):
        """IssueComments are unique based on their body
        """
        return (self.body, None)

    def __eq__(self, other):
        return self.body == other.body

    def __repr__(self):
        return u"{}(body={}".format(self.__class__.__name__,
                                    self.body)


class InfoComment(IssueComment):
    level = LEVEL_INFO


class Comment(BaseComment):
    """A line comment on the pull request.

    The `line` attribute is populated when comments are built
    from tool output.

    The `line` attribute is then mapped into a `position` when
    a comment is merged with diff data.
    """
    line = 0
    position = 0
    body = ''
    filename = ''

    # Sigil value for pushing a comment to the first
    # line in file's diff. This is used by linters
    # that need to output warnings for a file not a
    # specific line.
    FIRST_LINE_IN_DIFF = -2

    def __init__(self, filename='', line=0, position=0, body=''):
        self.body = body
        self.line = line
        self.filename = filename
        self.position = position or 0

    def payload(self):
        """Generate payload for comment based reviews"""
        return {
            'path': self.filename,
            'position': self.position,
            'body': self.body,
        }

    def checkrun_payload(self):
        """Generate payload for checks based review."""
        payload = {
            'path': self.filename,
            'start_line': self.line,
            'end_line': self.line,
            'message': self.body,
            # TODO extract this data for linters that support it
            'annotation_level': 'failure',
        }
        return payload

    def key(self):
        offset = self.position if self.position else self.line
        return (self.filename, offset)

    def summary_text(self):
        return u"{0.filename}, line {0.line} - {0.body}".format(self)

    def __eq__(self, other):
        return (self.filename == other.filename and
                self.position == other.position and
                self.body == other.body)

    def __repr__(self):
        return "%s(filename=%s, line=%s, position=%s, body=%s)" % (
            str(self.__class__.__name__),
            self.filename,
            self.line,
            self.position,
            self.body)


class Review(object):
    """
    Holds the comments from a review can
    add/track problems logged and post new problems
    to github.
    """

    def __init__(self, repo, pull_request, config):
        self._repo = repo
        self._comments = Problems()
        # TODO add diff collection to the review so that state is in fewer places.
        # TODO rename to self.pull
        self._pull = pull_request
        self.config = config

    def comments(self, filename):
        return self._comments.all(filename)

    def publish(self, problems, check_run_id=None, logs=None):
        """
        Publish the review.

        Use the check_run_id to either publish a check suite result
        or a commit status (deprecated)

        The optional `logs` parameter is used by checkrun publishing
        to update the result description with the logs.
        """
        problems.limit_to_changes()
        if check_run_id:
            self._publish_checkrun(problems, check_run_id, logs)
        else:
            self._publish_review(problems, self._pull.head)

    def _publish_checkrun(self, problems, check_run_id, logs):
        """Publish the review as a checkrun

        GitHub check-runs require a GitHub app which isn't
        supported by lint-review directly but is supported
        by stickler-ci.
        """
        comment_count = len(problems)
        buildlog.info('Publishing %s new comments', comment_count)
        log.info("Publishing result for checkrun=%s. %s new comments for %s",
                 check_run_id,
                 comment_count,
                 self._pull.display_name)

        has_problems = problems.error_count() > 0
        self._remove_ok_label()

        def build_annotations(chunk):
            # Convert line comments into the format
            # GitHub checkrun annotations need.
            return [
                comment.checkrun_payload()
                for comment in chunk
                if isinstance(comment, Comment)
            ]

        # GitHub only accepts 50 annotations per request so we
        # need to chunk it up.
        annotation_payloads = [
            build_annotations(chunk)
            for chunk in problems.iter_chunks(50)
        ]
        summary = [
            comment.body
            for comment in problems
            if isinstance(comment, IssueComment)
        ]

        conclusion = self.config.failed_review_status()
        title = 'Review failed'
        if not has_problems:
            conclusion = 'success'
            title = 'Review Passed'

        check_data = {
            'conclusion': conclusion,
            'title': title,
            'text': '',
            'summary': '',
        }

        if len(summary):
            check_data['summary'] = "\n\n".join(
                ["Your linters output the following general problems:"] +
                summary
            ).strip()

        if logs:
            check_data['text'] = """
<details>
<summary>Review Logs</summary>
<pre>
{}
</pre>
</details>
""".format(logs)

        # Some reviews have no comments and should be marked as success.
        if not (summary or annotation_payloads):
            review = self._build_checkrun(0, annotation_payloads, check_data)
            self._repo.update_checkrun(check_run_id, review)

        for i, chunk in enumerate(annotation_payloads):
            review = self._build_checkrun(i, chunk, check_data)
            self._repo.update_checkrun(check_run_id, review)

    def _build_checkrun(self, index, comments, check_data):
        """Because github3.py doesn't support creating checkruns
        we use some workarounds.
        """
        # Publish metadata on the first chunk. Subsequent
        # chunks only append annotations.
        if index == 0:
            return {
                'conclusion': check_data['conclusion'],
                'completed_at': datetime.utcnow().isoformat() + 'Z',
                'output': {
                    'title': check_data['title'],
                    'summary': check_data['summary'],
                    'text': check_data['text'],
                    'annotations': comments
                },
            }
        # Update the checkrun with additional annotations.
        return {
            'output': {
                'title': check_data['title'],
                'summary': check_data['summary'],
                'text': check_data['text'],
                'annotations': comments
            }
        }

    def _publish_review(self, problems, head_sha):
        """Publish the review as a pull request review.

        Existing comments are loaded, and compared
        to new problems. Once the new unique problems
        are distilled new comments are published.
        """
        # If the pull request has no changes notify why
        if not problems.has_changes():
            return self._publish_empty_comment()

        has_problems = problems.error_count() > 0

        # If we are submitting a comment review
        # we drop comments that have already been posted.
        existing_comments = self.load_comments()

        # Remove comments we made in the past, so that we only
        # post previously un-reported issues. We assume that comments
        # that with the same line and body are from us.
        for comment in existing_comments:
            problems.remove(comment)
        new_problem_count = len(problems)

        threshold = self.config.summary_threshold()
        under_threshold = (threshold is None or
                           new_problem_count < threshold)

        if under_threshold:
            self._publish_pull_review(problems, head_sha)
        else:
            self._publish_summary(problems)
        self.publish_status(has_problems)

    def load_comments(self):
        """Load the existing comments on a pull request
        Return a Problems instance with the existing review comments.
        """
        log.debug("Loading comments for pull request '%s'", self._pull.number)
        existing = Problems()
        comments = list(self._pull.review_comments())

        for comment in comments:
            # Workaround github3 not exposing attributes for what we need.
            guts = comment.as_dict()
            filename = guts['path']
            if not guts['position']:
                log.debug("Ignoring outdated diff comment '%s'", comment.id)
                continue
            existing.add(
                filename,
                None,
                comment.body,
                int(guts['position']))
        log.debug("'%s' comments loaded", len(existing))
        return existing

    def _publish_pull_review(self, problems, head_commit):
        """Publish the issues contains in the problems
        parameter. changes is used to fetch the commit sha
        for the comments on a given file.
        """
        comment_count = len(problems)
        buildlog.info('Publishing %s new comments', comment_count)
        log.info("Publishing review of %s new comments for %s",
                 comment_count,
                 self._pull.display_name)
        self._remove_ok_label()
        review = self._build_review(problems, head_commit)
        if len(review['comments']) or len(review['body']):
            self._pull.create_review(review)

    def _build_review(self, problems, head_commit):
        """Because github3.py doesn't support creating reviews
        we use some workarounds
        """
        body = [
            comment.body
            for comment in problems
            if isinstance(comment, IssueComment)
        ]
        comments = [
            comment.payload()
            for comment in problems
            if isinstance(comment, Comment)
        ]
        review = {
            'commit_id': head_commit,
            'event': 'COMMENT',
            'body': "\n\n".join(body),
            'comments': comments
        }
        return review

    def publish_status(self, has_problems):
        """Update the build status for the tip commit.
        The build will be a success if there are 0 problems,
        or if the review configuration coerces failures into
        success.
        """
        state = self.config.failed_review_status()
        description = 'Lint errors found, see pull request comments.'
        if not has_problems:
            self._publish_ok_label()
            self._publish_ok_comment()
            state = 'success'
            description = 'No lint errors found.'
        self._repo.create_status(
            self._pull.head,
            state,
            description
        )

    def _remove_ok_label(self):
        label = self.config.passed_review_label()
        if label:
            IssueLabel(label).remove(self._pull)

    def _publish_ok_label(self):
        """Optionally publish the OK_LABEL if it is enabled.
        """
        label = self.config.passed_review_label()
        if label:
            issue_label = IssueLabel(label)
            issue_label.publish(self._repo, self._pull)

    def _publish_ok_comment(self):
        """Optionally publish the OK_COMMENT if it is enabled.
        """
        comment = self.config.get('OK_COMMENT', False)
        if comment:
            self._pull.create_comment(comment)

    def _publish_empty_comment(self):
        log.info('Publishing empty comment.')
        self._remove_ok_label()
        body = ('Could not review pull request. '
                'It may be too large, or contain no reviewable changes.')
        self._pull.create_comment(body)
        self._repo.create_status(
            self._pull.head,
            'success',
            body
        )

    def _publish_summary(self, problems):
        num_comments = len(problems)
        log.info('Publishing summary comment for %s errors', num_comments)

        self._remove_ok_label()
        body = u"There are {0} errors:\n\n".format(num_comments)
        for problem in problems:
            body += u"* {}\n".format(problem.summary_text())
        self._pull.create_comment(body)


class Problems(object):
    """Collection class for holding all the problems found
    during automated review.

    Used by tool objects to collect problems, and by
    the Review objects to publish results.
    """

    def __init__(self, changes=None):
        self._items = OrderedDict()
        self._changes = changes

    def set_changes(self, changes):
        self._changes = changes

    def has_changes(self):
        return self._changes and len(self._changes) > 0

    def line_to_position(self, filename, line):
        """Convert the line number in the final file to a diff offset

        Saving comments in github requires line offsets not line numbers.
        Mapping line numbers makes saving possible.
        """
        if not self._changes:
            return line
        return self._changes.line_position(filename, line)

    def all(self, filename=None):
        if filename:
            return [error
                    for error in self
                    if hasattr(error, 'filename') and
                    error.filename == filename]
        return list(self._items.values())

    def add(self, filename, line=None, body=None, position=None):
        """Add a problem to the review.

        If position is not supplied the diff collection will be scanned
        and the line numbers diff offset will be fetched from there.
        """
        if isinstance(filename, BaseComment):
            self._items[filename.key()] = filename
            return

        if line == 0:
            line = Comment.FIRST_LINE_IN_DIFF
        if not position:
            position = self.line_to_position(filename, line)

        error = Comment(
            filename=filename,
            line=line,
            position=position,
            body=body)
        key = error.key()
        if key not in self._items:
            log.debug("Adding new line comment '%s'", error)
            self._items[key] = error
        else:
            log.debug("Updating existing line comment with '%s'", error)
            self._items[key].append_body(error.body)

    def add_many(self, problems):
        """Add multiple problems to the review.
        """
        for p in problems:
            self.add(p)

    def limit_to_changes(self):
        """Limit the contained problems to only those changed
        in the DiffCollection
        """
        changes = self._changes

        def sieve(err):
            if not hasattr(err, 'filename'):
                return True
            if err.line == Comment.FIRST_LINE_IN_DIFF:
                lineno = changes.first_changed_line(err.filename)
                err.line = lineno
                err.position = changes.line_position(err.filename, lineno)
            if changes and changes.has_line_changed(err.filename, err.line):
                return True
            return False

        items = OrderedDict()
        for error in self:
            if sieve(error):
                items[error.key()] = error
        self._items = items

    def remove(self, comment):
        """Remove a problem from the list based on the filename
        position and comment.
        """
        found = False
        for i, item in self._items.items():
            if item == comment:
                found = i
                break
        if found is not False:
            del self._items[found]

    def error_count(self):
        return len([e for e in self._items.values() if e.level == LEVEL_ERROR])

    def iter_chunks(self, size=50):
        """Split the problems into chunks
        Useful when publishing as a checkrun result.
        """
        values = list(self._items.values())
        for i in range(0, len(values), size):
            yield values[i:i+size]

    def __len__(self):
        return len(self._items.values())

    def __iter__(self):
        for item in self._items.values():
            yield item
