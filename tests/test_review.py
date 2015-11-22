from . import load_fixture
from contextlib import contextmanager
from lintreview.config import load_config
from lintreview.diff import DiffCollection
from lintreview.review import Review
from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.review import IssueComment
from mock import patch, Mock, call
from nose.tools import eq_
from github3.issues.comment import IssueComment as GhIssueComment
from github3.pulls import PullFile
from requests.models import Response
from unittest import TestCase
import json

config = load_config()


class TestReview(TestCase):

    def setUp(self):
        pr = Mock()
        issue = Mock()
        gh = Mock()

        gh.pull_request.return_value = pr
        gh.issue.return_value = issue

        self.gh, self.pr, self.issue = gh, pr, issue
        self.review = Review(self.gh, 2)

    def test_ensure_correct_pull_request_loaded(self):
        # Test the setup setup.
        self.gh.pull_request.assert_called_with(2)

    def test_load_comments__none_active(self):
        fixture_data = load_fixture('comments_none_current.json')
        self.pr.review_comments.return_value = map(
            lambda f: GhIssueComment(f),
            json.loads(fixture_data))

        review = Review(self.gh, 2)
        review.load_comments()

        eq_(0, len(review.comments("View/Helper/AssetCompressHelper.php")))

    def test_load_comments__loads_comments(self):
        fixture_data = load_fixture('comments_current.json')
        self.pr.review_comments.return_value = map(
            lambda f: GhIssueComment(f),
            json.loads(fixture_data))
        review = Review(self.gh, 2)
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
        review = Review(self.gh, 2)
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
        expected = Comment(filename_1, 87, 87, 'Something different')
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

        review = Review(self.gh, 3)
        review.publish_problems(problems, sha)

        assert self.pr.create_review_comment.called
        eq_(2, self.pr.create_review_comment.call_count)
        calls = self.pr.create_review_comment.call_args_list

        expected = call(
            commit_id=sha,
            path=errors[0][0],
            position=errors[0][1],
            body=errors[0][2]
        )
        eq_(calls[0], expected)

        expected = call(
            commit_id=sha,
            path=errors[1][0],
            position=errors[1][1],
            body=errors[1][2]
        )
        eq_(calls[1], expected)

    def test_publish_problems_add_ok_label(self):
        problems = Problems()

        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            (filename_1, 117, 'Something bad'),
            (filename_1, 119, 'Something bad'),
        )
        problems.add_many(errors)
        sha = 'abc123'

        review = Review(self.gh, 3)
        label = config.get('OK_LABEL', 'No lint errors')

        label_obj = Mock()
        label_obj.name = label
        self.issue.labels.return_value = (label_obj,)

        with add_ok_label(self.gh, 3, label):
            sha = 'abc123'
            review.publish_problems(problems, sha)

        assert self.issue.remove_label.called
        assert self.pr.create_review_comment.called
        eq_(2, self.pr.create_review_comment.call_count)
        assert_add_to_issue(self.gh)

        calls = self.issue.remove_label.call_args_list

        expected = call(label)
        eq_(calls, [expected])

        calls = self.pr.create_review_comment.call_args_list

        expected = call(
            commit_id=sha,
            path=errors[0][0],
            position=errors[0][1],
            body=errors[0][2]
        )
        eq_(calls[0], expected)

        expected = call(
            commit_id=sha,
            path=errors[1][0],
            position=errors[1][1],
            body=errors[1][2]
        )
        eq_(calls[1], expected)

    def test_publish_ok_comment(self):
        problems = Problems(changes=[1])
        review = Review(self.gh, 3)

        sha = 'abc123'
        review.publish(problems, sha)

        assert not(self.pr.create_review_comment.called)
        assert self.issue.create_comment.called

        calls = self.issue.create_comment.call_args_list

        expected = call(
            config.get('OK_COMMENT', ':+1: No lint errors found.'))
        eq_(calls[0], expected)

    def test_publish_ok_comment_add_ok_label(self):
        problems = Problems(changes=[1])
        review = Review(self.gh, 3)
        label = config.get('OK_LABEL', 'No lint errors')

        label_obj = Mock()
        label_obj.name = label
        self.issue.labels.return_value = (label_obj,)

        with add_ok_label(self.gh, 3, label, create=True):
            sha = 'abc123'
            review.publish(problems, sha)

        assert not self.issue.create_comment.called
        assert not self.issue.create_comment.called
        assert self.issue.remove_label.called

        calls = self.issue.remove_label.call_args_list

        expected = call(label)
        eq_(calls, [expected])

        assert_add_to_issue(self.gh, 3, label, create=True)
        assert not(self.issue.create_comment.called)

    def test_publish_empty_comment(self):
        problems = Problems(changes=[])
        review = Review(self.gh, 3)

        sha = 'abc123'
        review.publish(problems, sha)

        assert self.issue.create_comment.called

        calls = self.issue.create_comment.call_args_list

        msg = ('Could not review pull request. '
               'It may be too large, or contain no reviewable changes.')
        expected = call(msg)
        eq_(calls[0], expected)

    def test_publish_empty_comment_add_ok_label(self):
        problems = Problems(changes=[])
        review = Review(self.gh, 3)
        label = config.get('OK_LABEL', 'No lint errors')

        with add_ok_label(self.gh, 3, label):
            sha = 'abc123'
            review.publish(problems, sha)

        assert self.issue.create_comment.called, 'ok comment should be added.'
        assert self.issue.remove_label.called, 'label should be removed.'
        self.issue.remove_label.assert_called_with(label)

        assert_add_to_issue(self.gh)
        msg = ('Could not review pull request. '
               'It may be too large, or contain no reviewable changes.')
        self.issue.create_comment.assert_called_with(msg)

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

        review = Review(self.gh, 3)
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
        sha = 'abc123'

        review = Review(self.gh, 3)
        review.publish_summary(problems)

        assert self.issue.create_comment.called
        eq_(1, self.issue.create_comment.call_count)
        calls = self.issue.create_comment.call_args_list

        msg = """There are 2 errors:

* Console/Command/Task/AssetBuildTask.php, line 117 - Something bad
* Console/Command/Task/AssetBuildTask.php, line 119 - Something bad
"""
        expected = call(msg)
        eq_(calls[0], expected)


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


@contextmanager
def add_ok_label(gh, pr_number, *labels, **kw):
    from lintreview.review import config

    if labels:
        class Label(object):
            def __init__(self, name):
                self.name = name
        gh.issue().labels.return_value = [Label(n) for n in labels]

    gh.label.return_value = False;

    eq_(config["ADD_OK_LABEL"], False)
    config["ADD_OK_LABEL"] = True
    try:
        yield
    finally:
        config["ADD_OK_LABEL"] = False


def assert_add_to_issue(gh, *pr_number_and_labels, **kw):
    if not pr_number_and_labels:
        assert not gh.create_label.called
    else:
        import json
        pr_number = pr_number_and_labels[0]
        labels = list(pr_number_and_labels[1:])

        if kw.get("create"):
            expected = call(
                name=labels[0],
                color="bfe5bf",
            )
            eq_(gh.create_label.call_args_list, [expected])

        assert gh.issue().add_labels.called, 'OK label should be added'
        gh.issue().add_labels.assert_called_with(labels[0])
