from __future__ import absolute_import
from . import load_fixture
from lintreview.config import load_config
from lintreview.diff import DiffCollection
from lintreview.review import Review, Problems, Comment, IssueComment
from lintreview.repo import GithubRepository, GithubPullRequest
from mock import Mock
from nose.tools import eq_
from github3.issues.comment import IssueComment as GhIssueComment
from github3.pulls import PullFile
from unittest import TestCase
import json

config = load_config()


class TestReview(TestCase):

    def setUp(self):
        repo = Mock(spec=GithubRepository)
        pr = Mock(spec=GithubPullRequest,
                  head='abc123',
                  display_name='markstory/lint-review#1',
                  number=2)
        repo.pull_request.return_value = pr

        self.repo, self.pr = repo, pr
        self.review = Review(repo, pr)

    def test_load_comments__none_active(self):
        fixture_data = load_fixture('comments_none_current.json')
        self.pr.review_comments.return_value = [
                GhIssueComment(f) for f in json.loads(fixture_data)]

        review = Review(self.repo, self.pr)
        review.load_comments()

        eq_(0, len(review.comments("View/Helper/AssetCompressHelper.php")))

    def test_load_comments__loads_comments(self):
        fixture_data = load_fixture('comments_current.json')
        self.pr.review_comments.return_value = [
            GhIssueComment(f) for f in json.loads(fixture_data)]
        review = Review(self.repo, self.pr)
        review.load_comments()

        filename = "Routing/Filter/AssetCompressor.php"
        res = review.comments(filename)
        eq_(1, len(res))
        expected = Comment(filename, None, 87, "A pithy remark")
        eq_(expected, res[0])

        filename = "View/Helper/AssetCompressHelper.php"
        res = review.comments(filename)
        eq_(2, len(res))
        expected = Comment(filename, None, 40, "Some witty comment.")
        eq_(expected, res[0])

        expected = Comment(filename, None, 89, "Not such a good comment")
        eq_(expected, res[1])

    def test_filter_existing__removes_duplicates(self):
        fixture_data = load_fixture('comments_current.json')
        self.pr.review_comments.return_value = [
            GhIssueComment(f) for f in json.loads(fixture_data)]
        problems = Problems()
        review = Review(self.repo, self.pr)
        filename_1 = "Routing/Filter/AssetCompressor.php"
        filename_2 = "View/Helper/AssetCompressHelper.php"

        problems.add(filename_1, 87, 'A pithy remark')
        problems.add(filename_1, 87, 'Something different')
        problems.add(filename_2, 88, 'I <3 it')
        problems.add(filename_2, 89, 'Not such a good comment')

        review.load_comments()
        review.remove_existing(problems)

        res = problems.all(filename_1)
        eq_(1, len(res))
        expected = Comment(filename_1,
                           87,
                           87,
                           'A pithy remark\nSomething different')
        eq_(res[0], expected)

        res = problems.all(filename_2)
        eq_(1, len(res))
        expected = Comment(filename_2, 88, 88, 'I <3 it')
        eq_(res[0], expected)

    def test_publish_review(self):
        problems = Problems()

        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            Comment(filename_1, 117, 117, 'Something bad'),
            Comment(filename_1, 119, 119, 'Something bad'),
        )
        problems.add_many(errors)
        sha = 'abc123'

        review = Review(self.repo, self.pr)
        review.publish_review(problems, sha)

        assert self.pr.create_review.called
        eq_(1, self.pr.create_review.call_count)

        assert_review(
            self.pr.create_review.call_args,
            errors,
            sha)

    def test_publish_review__no_comments(self):
        problems = Problems()
        sha = 'abc123'

        review = Review(self.repo, self.pr)
        review.publish_review(problems, sha)

        assert self.pr.create_review.called is False

    def test_publish_review__only_issue_comment(self):
        problems = Problems()
        problems.add(IssueComment('Very bad'))
        sha = 'abc123'

        review = Review(self.repo, self.pr)
        review.publish_review(problems, sha)

        assert self.pr.create_review.called
        assert_review(
            self.pr.create_review.call_args,
            [],
            sha,
            body='Very bad')

    def test_publish__join_issue_comments(self):
        problems = Problems()

        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            IssueComment('First'),
            Comment(filename_1, 119, 119, 'Something bad'),
            IssueComment('Second'),
        )
        problems.add_many(errors)
        sha = 'abc123'

        review = Review(self.repo, self.pr)
        review.publish_review(problems, sha)

        assert self.pr.create_review.called
        eq_(1, self.pr.create_review.call_count)

        assert_review(
            self.pr.create_review.call_args,
            [errors[1]],
            sha,
            body='First\n\nSecond')

    def test_publish_status__ok_no_comment_label_or_status(self):
        config = {
            'OK_COMMENT': None,
            'OK_LABEL': None,
            'PULLREQUEST_STATUS': False,
        }
        review = Review(self.repo, self.pr, config)
        review.publish_status(0)

        assert not self.repo.create_status.called, 'Create status called'
        assert not self.pr.create_comment.called, 'Comment not created'
        assert not self.pr.add_label.called, 'Label added created'

    def test_publish_status__ok_with_comment_label_and_status(self):
        config = {
            'OK_COMMENT': 'Great job!',
            'OK_LABEL': 'No lint errors',
            'PULLREQUEST_STATUS': True,
        }
        review = Review(self.repo, self.pr, config)
        review.publish_status(0)

        assert self.repo.create_status.called, 'Create status not called'
        self.repo.create_status.assert_called_with(
            self.pr.head,
            'success',
            'No lint errors found.')

        assert self.pr.create_comment.called, 'Issue comment created'
        self.pr.create_comment.assert_called_with('Great job!')

        assert self.pr.add_label.called, 'Label added created'
        self.pr.add_label.assert_called_with('No lint errors')

    def test_publish_status__has_errors(self):
        config = {
            'OK_COMMENT': 'Great job!',
            'OK_LABEL': 'No lint errors',
            'APP_NAME': 'custom-name'
        }
        review = Review(self.repo, self.pr, config)
        review.publish_status(1)

        assert self.repo.create_status.called, 'Create status not called'

        self.repo.create_status.assert_called_with(
            self.pr.head,
            'failure',
            'Lint errors found, see pull request comments.')
        assert not self.pr.create_comment.called, 'Comment not created'
        assert not self.pr.add_label.called, 'Label added created'

    def test_publish_review_remove_ok_label(self):
        problems = Problems()

        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            Comment(filename_1, 117, 117, 'Something bad'),
            Comment(filename_1, 119, 119, 'Something bad'),
        )
        problems.add_many(errors)
        sha = 'abc123'
        config = {'OK_LABEL': 'No lint'}

        review = Review(self.repo, self.pr, config)
        sha = 'abc123'
        review.publish_review(problems, sha)

        assert self.pr.remove_label.called, 'Label should be removed'
        assert self.pr.create_review.called, 'Review should be added'
        eq_(1, self.pr.create_review.call_count)

        self.pr.remove_label.assert_called_with(config['OK_LABEL'])
        assert_review(
            self.pr.create_review.call_args,
            errors,
            sha)

    def test_publish_empty_comment(self):
        problems = Problems(changes=[])
        review = Review(self.repo, self.pr)

        sha = 'abc123'
        review.publish(problems, sha)

        assert self.pr.create_comment.called, 'Should create a comment'

        msg = ('Could not review pull request. '
               'It may be too large, or contain no reviewable changes.')
        self.pr.create_comment.assert_called_with(msg)

    def test_publish_empty_comment_add_ok_label(self):
        problems = Problems(changes=[])
        config = {'OK_LABEL': 'No lint'}
        review = Review(self.repo, self.pr, config)

        sha = 'abc123'
        review.publish(problems, sha)

        assert self.pr.create_comment.called, 'ok comment should be added.'
        assert self.pr.remove_label.called, 'label should be removed.'
        self.pr.remove_label.assert_called_with(config['OK_LABEL'])

        msg = ('Could not review pull request. '
               'It may be too large, or contain no reviewable changes.')
        self.pr.create_comment.assert_called_with(msg)

    def test_publish_empty_comment_with_comment_status(self):
        config = {
            'PULLREQUEST_STATUS': True,
        }

        problems = Problems(changes=[])
        review = Review(self.repo, self.pr, config)

        sha = 'abc123'
        review.publish(problems, sha)

        assert self.pr.create_comment.called, 'Should create a comment'

        msg = ('Could not review pull request. '
               'It may be too large, or contain no reviewable changes.')

        self.repo.create_status.assert_called_with(
            self.pr.head,
            'error',
            msg)

        self.pr.create_comment.assert_called_with(msg)

    def test_publish_comment_threshold_checks(self):
        fixture = load_fixture('comments_current.json')
        self.pr.review_comments.return_value = [
            GhIssueComment(f) for f in json.loads(fixture)]

        problems = Problems()

        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            Comment(filename_1, 117, 117, 'Something bad'),
            Comment(filename_1, 119, 119, 'Something bad'),
        )
        problems.add_many(errors)
        problems.set_changes([1])
        sha = 'abc123'

        review = Review(self.repo, self.pr)
        review.publish_summary = Mock()
        review.publish(problems, sha, 1)

        assert review.publish_summary.called, 'Should have been called.'

    def test_publish_summary(self):
        problems = Problems()

        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            Comment(filename_1, 117, 117, 'Something bad'),
            Comment(filename_1, 119, 119, 'Something bad'),
        )
        problems.add_many(errors)
        problems.set_changes([1])

        review = Review(self.repo, self.pr)
        review.publish_summary(problems)

        assert self.pr.create_comment.called
        eq_(1, self.pr.create_comment.call_count)

        msg = """There are 2 errors:

* Console/Command/Task/AssetBuildTask.php, line 117 - Something bad
* Console/Command/Task/AssetBuildTask.php, line 119 - Something bad
"""
        self.pr.create_comment.assert_called_with(msg)


class TestProblems(TestCase):

    two_files_json = load_fixture('two_file_pull_request.json')

    # Block offset so lines don't match offsets
    block_offset = load_fixture('pull_request_line_offset.json')

    def setUp(self):
        self.problems = Problems()

    def test_add(self):
        self.problems.add('file.py', 10, 'Not good')
        eq_(1, len(self.problems))

        self.problems.add('file.py', 11, 'Not good')
        eq_(2, len(self.problems))
        eq_(2, len(self.problems.all()))
        eq_(2, len(self.problems.all('file.py')))
        eq_(0, len(self.problems.all('not there')))

    def test_add__duplicate_is_ignored(self):
        self.problems.add('file.py', 10, 'Not good')
        eq_(1, len(self.problems))

        self.problems.add('file.py', 10, 'Not good')
        eq_(1, len(self.problems))

    def test_add__same_line_combines(self):
        self.problems.add('file.py', 10, 'Tabs bad')
        self.problems.add('file.py', 10, 'Spaces are good')
        eq_(1, len(self.problems))

        result = self.problems.all()
        expected = 'Tabs bad\nSpaces are good'
        eq_(expected, result[0].body)

    def test_add__same_line_ignores_duplicates(self):
        self.problems.add('file.py', 10, 'Tabs bad')
        self.problems.add('file.py', 10, 'Tabs bad')
        eq_(1, len(self.problems))

        result = self.problems.all()
        expected = 'Tabs bad'
        eq_(expected, result[0].body)

    def test_add__with_base_path(self):
        problems = Problems('/some/path/')
        problems.add('/some/path/file.py', 10, 'Not good')
        eq_([], problems.all('/some/path/file.py'))
        eq_(1, len(problems.all('file.py')))
        eq_(1, len(problems))

    def test_add__with_base_path_no_trailing_slash(self):
        problems = Problems('/some/path')
        problems.add('/some/path/file.py', 10, 'Not good')
        eq_([], problems.all('/some/path/file.py'))
        eq_(1, len(problems.all('file.py')))
        eq_(1, len(problems))

    def test_add__with_diff_containing_block_offset(self):
        res = [PullFile(f) for f in json.loads(self.block_offset)]
        changes = DiffCollection(res)

        problems = Problems(changes=changes)
        line_num = 32
        problems.add('somefile.py', line_num, 'Not good')
        eq_(1, len(problems))

        result = problems.all('somefile.py')
        eq_(changes.line_position('somefile.py', line_num), result[0].position,
            'Offset should be transformed to match value in changes')

    def test_add_many(self):
        errors = [
            Comment('some/file.py', 10, 10, 'Thing is wrong'),
            Comment('some/file.py', 12, 12, 'Not good'),
        ]
        self.problems.add_many(errors)
        result = self.problems.all('some/file.py')
        eq_(2, len(result))
        eq_(errors, result)

    def test_limit_to_changes__remove_problems(self):
        res = [PullFile(f) for f in json.loads(self.two_files_json)]
        changes = DiffCollection(res)

        # Setup some fake problems.
        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            Comment(None, None, None, 'This is a general comment'),
            Comment(filename_1, 117, 117, 'Something bad'),
            Comment(filename_1, 119, 119, 'Something else bad'),
            Comment(filename_1, 130, 130, 'Filtered out, line is not changed'),
        )
        self.problems.add_many(errors)
        filename_2 = 'Test/test_files/View/Parse/single.ctp'
        errors = (
            Comment(filename_2, 2, 2, 'Filtered out'),
            Comment(filename_2, 3, 3, 'Something bad'),
            Comment(filename_2, 7, 7, 'Filtered out'),
        )
        self.problems.add_many(errors)
        self.problems.set_changes(changes)
        self.problems.limit_to_changes()

        result = self.problems.all(filename_1)
        eq_(2, len(result))
        expected = [
            Comment(filename_1, 117, 117, 'Something bad'),
            Comment(filename_1, 119, 119, 'Something else bad')]
        eq_(len(result), len(expected))
        eq_(result, expected)

        result = self.problems.all(filename_2)
        eq_(1, len(result))
        expected = [
            Comment(filename_2, 3, 3, 'Something bad')
        ]
        eq_(result, expected)

    def test_has_changes(self):
        problems = Problems(changes=None)
        self.assertFalse(problems.has_changes())

        problems = Problems(changes=[1])
        assert problems.has_changes()


def assert_review(call_args, errors, sha, body=''):
    """
    Check that the review comments match the error list.
    """
    actual = call_args[0][0]
    comments = [error.payload() for error in errors]
    expected = {
        'commit_id': sha,
        'event': 'COMMENT',
        'body': body,
        'comments': comments
    }
    eq_(actual.keys(), expected.keys())
    eq_(len(comments),
        len(actual['comments']),
        'Error and comment counts are off.')
