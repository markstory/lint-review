from . import load_fixture
from contextlib import contextmanager
from lintreview.config import load_config
from lintreview.diff import DiffCollection
from lintreview.review import Review, Problems, Comment
from lintreview.repo import GithubRepository, GithubPullRequest
from mock import Mock, call
from nose.tools import eq_
from github3.issues.comment import IssueComment as GhIssueComment
from github3.pulls import PullFile
from unittest import TestCase
import json

config = load_config()


class TestReview(TestCase):

    def setUp(self):
        repo = Mock(spec=GithubRepository)
        pr = Mock(spec=GithubPullRequest, head='abc123', number=2)
        repo.pull_request.return_value = pr

        self.repo, self.pr = repo, pr
        self.review = Review(repo, pr)

    def test_load_comments__none_active(self):
        fixture_data = load_fixture('comments_none_current.json')
        self.pr.review_comments.return_value = map(
            lambda f: GhIssueComment(f),
            json.loads(fixture_data))

        review = Review(self.repo, self.pr)
        review.load_comments()

        eq_(0, len(review.comments("View/Helper/AssetCompressHelper.php")))

    def test_load_comments__loads_comments(self):
        fixture_data = load_fixture('comments_current.json')
        self.pr.review_comments.return_value = map(
            lambda f: GhIssueComment(f),
            json.loads(fixture_data))
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
        self.pr.review_comments.return_value = map(
            lambda f: GhIssueComment(f),
            json.loads(fixture_data))
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

    def test_publish_problems(self):
        problems = Problems()

        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            (filename_1, 117, 'Something bad'),
            (filename_1, 119, 'Something bad'),
        )
        problems.add_many(errors)
        sha = 'abc123'

        review = Review(self.repo, self.pr)
        review.publish_problems(problems, sha)

        assert self.pr.create_review_comment.called
        eq_(2, self.pr.create_review_comment.call_count)

        assert_review_comments_created(
            self.pr.create_review_comment.call_args_list,
            errors,
            sha)

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

    def test_publish_problems_remove_ok_label(self):
        problems = Problems()

        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            (filename_1, 117, 'Something bad'),
            (filename_1, 119, 'Something bad'),
        )
        problems.add_many(errors)
        sha = 'abc123'
        config = {'OK_LABEL': 'No lint'}

        review = Review(self.repo, self.pr, config)
        sha = 'abc123'
        review.publish_problems(problems, sha)

        assert self.pr.remove_label.called, 'Label should be removed'
        assert self.pr.create_review_comment.called, 'Comments should be added'
        eq_(2, self.pr.create_review_comment.call_count)

        self.pr.remove_label.assert_called_with(config['OK_LABEL'])
        assert_review_comments_created(
            self.pr.create_review_comment.call_args_list,
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

    def test_publish_comment_threshold_checks(self):
        fixture = load_fixture('comments_current.json')
        self.pr.review_comments.return_value = map(
            lambda f: GhIssueComment(f),
            json.loads(fixture))

        problems = Problems()

        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            (filename_1, 117, 'Something bad'),
            (filename_1, 119, 'Something bad'),
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
            (filename_1, 117, 'Something bad'),
            (filename_1, 119, 'Something bad'),
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
        for item in self.problems:
            print item
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
        res = map(lambda f: PullFile(f),
                  json.loads(self.block_offset))
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
            ('some/file.py', 10, 'Thing is wrong'),
            ('some/file.py', 12, 'Not good'),
        ]
        self.problems.add_many(errors)
        result = self.problems.all('some/file.py')
        eq_(2, len(result))
        expected = [
            Comment(errors[0][0], errors[0][1], errors[0][1], errors[0][2]),
            Comment(errors[1][0], errors[1][1], errors[1][1], errors[1][2]),
        ]
        eq_(expected, result)

    def test_limit_to_changes__remove_problems(self):
        res = map(lambda f: PullFile(f),
                  json.loads(self.two_files_json))
        changes = DiffCollection(res)

        # Setup some fake problems.
        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            (None, None, 'This is a general comment'),
            (filename_1, 117, 'Something bad'),
            (filename_1, 119, 'Something else bad'),
            (filename_1, 130, 'Filtered out, as line is not changed'),
        )
        self.problems.add_many(errors)
        filename_2 = 'Test/test_files/View/Parse/single.ctp'
        errors = (
            (filename_2, 2, 'Filtered out'),
            (filename_2, 3, 'Something bad'),
            (filename_2, 7, 'Filtered out'),
        )
        self.problems.add_many(errors)
        self.problems.set_changes(changes)
        self.problems.limit_to_changes()

        result = self.problems.all(filename_1)
        eq_(2, len(result))
        expected = [
            (None, None, 'This is a general comment'),
            (filename_1, 117, 'Something bad'),
            (filename_1, 119, 'Something else bad')]
        eq_(result.sort(), expected.sort())

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


def assert_review_comments_created(call_args, errors, sha):
    """
    Check that the review comments match the error list.
    """
    eq_(len(call_args), len(errors), 'Errors and comment counts are off')
    for i, err in enumerate(errors):
        expected = call(
            commit_id=sha,
            path=err[0],
            position=err[1],
            body=err[2])
        eq_(expected, call_args[i])
