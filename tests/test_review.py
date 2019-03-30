from __future__ import absolute_import
import json
from unittest import TestCase
from mock import Mock, patch

from . import load_fixture, fixer_ini
from lintreview.config import load_config, build_review_config
from lintreview.diff import DiffCollection
from lintreview.review import Review, Problems, Comment, IssueComment
from lintreview.repo import GithubRepository, GithubPullRequest
from github3.issues.comment import IssueComment as GhIssueComment
from github3.pulls import PullFile
from github3.session import GitHubSession

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
        self.config = build_review_config(fixer_ini, config)

        self.session = GitHubSession()

    def test_review_repr(self):
        comment = Comment('afile.txt', None, 40, "Some witty comment.")
        self.assertIn('Comment(filename=', str(comment))

    def test_load_comments__none_active(self):
        fixture_data = load_fixture('comments_none_current.json')
        self.pr.review_comments.return_value = [
            GhIssueComment(f, self.session) for f in json.loads(fixture_data)
        ]

        review = Review(self.repo, self.pr, self.config)
        review.load_comments()

        filename = "View/Helper/AssetCompressHelper.php"
        self.assertEqual(0, len(review.comments(filename)))

    def test_load_comments__loads_comments(self):
        fixture_data = load_fixture('comments_current.json')
        self.pr.review_comments.return_value = [
            GhIssueComment(f, self.session) for f in json.loads(fixture_data)
        ]
        review = Review(self.repo, self.pr, self.config)
        review.load_comments()

        filename = "Routing/Filter/AssetCompressor.php"
        res = review.comments(filename)
        self.assertEqual(1, len(res))
        expected = Comment(filename, None, 87, "A pithy remark")
        self.assertEqual(expected, res[0])

        filename = "View/Helper/AssetCompressHelper.php"
        res = review.comments(filename)
        self.assertEqual(2, len(res))
        expected = Comment(filename, None, 40, "Some witty comment.")
        self.assertEqual(expected, res[0])

        expected = Comment(filename, None, 89, "Not such a good comment")
        self.assertEqual(expected, res[1])

    def test_filter_existing__removes_duplicates(self):
        fixture_data = load_fixture('comments_current.json')
        self.pr.review_comments.return_value = [
            GhIssueComment(f, self.session) for f in json.loads(fixture_data)
        ]
        problems = Problems()
        review = Review(self.repo, self.pr, self.config)
        filename_1 = "Routing/Filter/AssetCompressor.php"
        filename_2 = "View/Helper/AssetCompressHelper.php"

        problems.add(filename_1, 87, 'A pithy remark')
        problems.add(filename_1, 87, 'Something different')
        problems.add(filename_2, 88, 'I <3 it')
        problems.add(filename_2, 89, 'Not such a good comment')

        review.load_comments()
        review.remove_existing(problems)

        res = problems.all(filename_1)
        self.assertEqual(1, len(res))
        expected = Comment(filename_1,
                           87,
                           87,
                           'A pithy remark\nSomething different')
        self.assertEqual(res[0], expected)

        res = problems.all(filename_2)
        self.assertEqual(1, len(res))
        expected = Comment(filename_2, 88, 88, 'I <3 it')
        self.assertEqual(res[0], expected)

    def test_publish_pull_review(self):
        problems = Problems()

        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            Comment(filename_1, 117, 117, 'Something bad'),
            Comment(filename_1, 119, 119, 'Something bad'),
        )
        problems.add_many(errors)
        sha = 'abc123'

        review = Review(self.repo, self.pr, self.config)
        review.publish_pull_review(problems, sha)

        assert self.pr.create_review.called
        self.assertEqual(1, self.pr.create_review.call_count)

        assert_review(
            self,
            self.pr.create_review.call_args,
            errors,
            sha)

    def test_publish_pull_review__no_comments(self):
        problems = Problems()
        sha = 'abc123'

        review = Review(self.repo, self.pr, self.config)
        review.publish_pull_review(problems, sha)

        assert self.pr.create_review.called is False

    def test_publish_pull_review__only_issue_comment(self):
        problems = Problems()
        problems.add(IssueComment('Very bad'))
        sha = 'abc123'

        review = Review(self.repo, self.pr, self.config)
        review.publish_pull_review(problems, sha)

        assert self.pr.create_review.called
        assert_review(
            self,
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

        review = Review(self.repo, self.pr, self.config)
        review.publish_pull_review(problems, sha)

        assert self.pr.create_review.called
        self.assertEqual(1, self.pr.create_review.call_count)

        assert_review(
            self,
            self.pr.create_review.call_args,
            [errors[1]],
            sha,
            body='First\n\nSecond')

    def test_publish_status__ok_no_comment_or_label(self):
        app_config = {
            'OK_COMMENT': None,
            'OK_LABEL': None,
            'PULLREQUEST_STATUS': False,
        }
        tst_config = build_review_config(fixer_ini, app_config)
        review = Review(self.repo, self.pr, tst_config)
        review.publish_status(False)

        assert self.repo.create_status.called, 'Create status called'
        assert not self.pr.create_comment.called, 'Comment not created'
        assert not self.pr.add_label.called, 'Label added created'

    def test_publish_status__ok_with_comment_label(self):
        app_config = {
            'OK_COMMENT': 'Great job!',
            'OK_LABEL': 'No lint errors',
            'PULLREQUEST_STATUS': True,
        }
        tst_config = build_review_config(fixer_ini, app_config)
        Review(self.repo, self.pr, tst_config)
        review = Review(self.repo, self.pr, tst_config)
        review.publish_status(False)

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
        app_config = {
            'OK_COMMENT': 'Great job!',
            'OK_LABEL': 'No lint errors',
            'APP_NAME': 'custom-name'
        }
        tst_config = build_review_config(fixer_ini, app_config)
        review = Review(self.repo, self.pr, tst_config)
        review.publish_status(True)

        assert self.repo.create_status.called, 'Create status not called'

        self.repo.create_status.assert_called_with(
            self.pr.head,
            'failure',
            'Lint errors found, see pull request comments.')
        assert not self.pr.create_comment.called, 'Comment not created'
        assert not self.pr.add_label.called, 'Label added created'

    def test_publish_status__has_errors__success_status(self):
        app_config = {
            'PULLREQUEST_STATUS': False,
            'OK_COMMENT': 'Great job!',
            'OK_LABEL': 'No lint errors',
            'APP_NAME': 'custom-name'
        }
        tst_config = build_review_config(fixer_ini, app_config)
        self.assertEqual('success', tst_config.failed_review_status(),
                         'config object changed')

        review = Review(self.repo, self.pr, tst_config)
        review.publish_status(True)

        assert self.repo.create_status.called, 'Create status not called'
        self.repo.create_status.assert_called_with(
            self.pr.head,
            'success',
            'Lint errors found, see pull request comments.')
        assert not self.pr.create_comment.called, 'Comment not created'
        assert not self.pr.add_label.called, 'Label added created'

    def test_publish_pull_review_remove_ok_label(self):
        problems = Problems()

        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            Comment(filename_1, 117, 117, 'Something bad'),
            Comment(filename_1, 119, 119, 'Something bad'),
        )
        problems.add_many(errors)
        tst_config = build_review_config(fixer_ini, {'OK_LABEL': 'No lint'})

        review = Review(self.repo, self.pr, tst_config)
        sha = 'abc123'
        review.publish_pull_review(problems, sha)

        assert self.pr.remove_label.called, 'Label should be removed'
        assert self.pr.create_review.called, 'Review should be added'
        self.assertEqual(1, self.pr.create_review.call_count)

        self.pr.remove_label.assert_called_with(tst_config['OK_LABEL'])
        assert_review(
            self,
            self.pr.create_review.call_args,
            errors,
            sha)

    def test_publish_review_empty_comment(self):
        problems = Problems(changes=DiffCollection([]))
        review = Review(self.repo, self.pr, self.config)

        sha = 'abc123'
        review.publish_review(problems, sha)

        assert self.pr.create_comment.called, 'Should create a comment'

        msg = ('Could not review pull request. '
               'It may be too large, or contain no reviewable changes.')
        self.pr.create_comment.assert_called_with(msg)

    def test_publish_review_empty_comment_add_ok_label(self):
        problems = Problems(changes=DiffCollection([]))
        tst_config = build_review_config(fixer_ini, {'OK_LABEL': 'No lint'})
        review = Review(self.repo, self.pr, tst_config)

        sha = 'abc123'
        review.publish_review(problems, sha)

        assert self.pr.create_comment.called, 'ok comment should be added.'
        assert self.pr.remove_label.called, 'label should be removed.'
        self.pr.remove_label.assert_called_with(tst_config['OK_LABEL'])

        msg = ('Could not review pull request. '
               'It may be too large, or contain no reviewable changes.')
        self.pr.create_comment.assert_called_with(msg)

    def test_publish_review_empty_comment_with_comment_status(self):
        tst_config = build_review_config(fixer_ini,
                                         {'PULLREQUEST_STATUS': True})

        problems = Problems(changes=DiffCollection([]))
        review = Review(self.repo, self.pr, tst_config)

        sha = 'abc123'
        review.publish_review(problems, sha)

        assert self.pr.create_comment.called, 'Should create a comment'

        msg = ('Could not review pull request. '
               'It may be too large, or contain no reviewable changes.')

        self.repo.create_status.assert_called_with(
            self.pr.head,
            'success',
            msg)

        self.pr.create_comment.assert_called_with(msg)

    def test_publish_review_comment_threshold_checks(self):
        fixture = load_fixture('comments_current.json')
        self.pr.review_comments.return_value = [
            GhIssueComment(f, self.session) for f in json.loads(fixture)
        ]

        problems = Problems()

        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            Comment(filename_1, 117, 117, 'Something bad'),
            Comment(filename_1, 119, 119, 'Something bad'),
        )
        problems.add_many(errors)
        problems.set_changes([1])
        sha = 'abc123'

        tst_config = build_review_config(fixer_ini, {'SUMMARY_THRESHOLD': 1})
        review = Review(self.repo, self.pr, tst_config)
        with patch('lintreview.review.Review.publish_summary') as pub_sum_mock:
            review.publish_review(problems, sha)

            self.assertTrue(pub_sum_mock.called)

    @patch('lintreview.review.Review.publish_summary')
    @patch('lintreview.review.Review.publish_status')
    def test_publish_review_no_count_change(self, pub_status_mock, _):
        fixture = load_fixture('comments_current.json')
        self.pr.review_comments.return_value = [
            GhIssueComment(f, self.session) for f in json.loads(fixture)]
        problems = Problems()

        # Match the line/positions in comments_current.json
        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            Comment(filename_1, 40, 40, '2. Something bad'),
            Comment(filename_1, 87, 87, '1. Something bad'),
            Comment(filename_1, 89, 89, '2. Something bad'),
        )
        problems.add_many(errors)
        problems.set_changes([1])
        sha = 'abc123'

        tst_config = build_review_config(fixer_ini, {'SUMMARY_THRESHOLD': 1})
        review = Review(self.repo, self.pr, tst_config)

        review.publish_review(problems, sha)
        # Ensure publish_status(True) means the status=failed
        pub_status_mock.assert_called_with(True)

    def test_publish_summary(self):
        problems = Problems()

        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            IssueComment('Terrible things'),
            Comment(filename_1, 117, 117, 'Something bad'),
            Comment(filename_1, 119, 119, 'Something bad'),
        )
        problems.add_many(errors)
        problems.set_changes([1])

        review = Review(self.repo, self.pr, self.config)
        review.publish_summary(problems)

        assert self.pr.create_comment.called
        self.assertEqual(1, self.pr.create_comment.call_count)

        msg = """There are 3 errors:

* Terrible things
* Console/Command/Task/AssetBuildTask.php, line 117 - Something bad
* Console/Command/Task/AssetBuildTask.php, line 119 - Something bad
"""
        self.pr.create_comment.assert_called_with(msg)

    def test_publish_checkrun(self):
        self.repo.create_checkrun = Mock()
        tst_config = build_review_config(fixer_ini,
                                         {'PULLREQUEST_STATUS': True})
        problems = Problems()
        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            Comment(filename_1, 117, 8, 'Something bad'),
            Comment(filename_1, 119, 9, 'Something worse'),
        )
        problems.add_many(errors)
        run_id = 42

        review = Review(self.repo, self.pr, tst_config)
        review.publish_checkrun(problems, run_id)

        assert self.repo.update_checkrun.called
        self.assertEqual(1, self.repo.update_checkrun.call_count)

        assert_checkrun(
            self,
            self.repo.update_checkrun.call_args,
            errors,
            run_id)
        assert self.repo.create_status.called is False, 'no status required'

    def test_publish_checkrun__has_errors_force_success_status(self):
        self.repo.create_checkrun = Mock()
        tst_config = build_review_config(fixer_ini,
                                         {'PULLREQUEST_STATUS': False})
        self.assertEqual('success', tst_config.failed_review_status(),
                         'config object changed')

        review = Review(self.repo, self.pr, tst_config)

        problems = Problems()
        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            Comment(filename_1, 117, 8, 'Something bad'),
            Comment(filename_1, 119, 9, 'Something worse'),
        )
        problems.add_many(errors)
        run_id = 42
        review.publish_checkrun(problems, run_id)

        assert self.repo.create_status.called is False, 'no status required'

        checkrun = self.repo.update_checkrun.call_args[0][1]
        self.assertEqual('success', checkrun['conclusion'])
        assert len(checkrun['output']['annotations']) > 0

    def test_publish_checkrun__no_problems(self):
        self.repo.create_checkrun = Mock()
        tst_config = build_review_config(fixer_ini,
                                         {'PULLREQUEST_STATUS': True})
        problems = Problems()
        run_id = 42

        review = Review(self.repo, self.pr, tst_config)
        review.publish_checkrun(problems, run_id)

        assert self.repo.update_checkrun.called
        self.assertEqual(1, self.repo.update_checkrun.call_count)

        assert_checkrun(
            self,
            self.repo.update_checkrun.call_args,
            [],
            run_id)
        assert self.repo.create_status.called is False, 'no status required'


class TestProblems(TestCase):

    two_files_json = load_fixture('two_file_pull_request.json')

    # Block offset so lines don't match offsets
    block_offset = load_fixture('pull_request_line_offset.json')

    def setUp(self):
        self.problems = Problems()
        self.session = GitHubSession()

    def test_add(self):
        self.problems.add('file.py', 10, 'Not good')
        self.assertEqual(1, len(self.problems))

        self.problems.add('file.py', 11, 'Not good')
        self.assertEqual(2, len(self.problems))
        self.assertEqual(2, len(self.problems.all()))
        self.assertEqual(2, len(self.problems.all('file.py')))
        self.assertEqual(0, len(self.problems.all('not there')))

    def test_add__duplicate_is_ignored(self):
        self.problems.add('file.py', 10, 'Not good')
        self.assertEqual(1, len(self.problems))

        self.problems.add('file.py', 10, 'Not good')
        self.assertEqual(1, len(self.problems))

    def test_add__same_line_combines(self):
        self.problems.add('file.py', 10, 'Tabs bad')
        self.problems.add('file.py', 10, 'Spaces are good')
        self.assertEqual(1, len(self.problems))

        result = self.problems.all()
        expected = 'Tabs bad\nSpaces are good'
        self.assertEqual(expected, result[0].body)

    def test_add__same_line_ignores_duplicates(self):
        self.problems.add('file.py', 10, 'Tabs bad')
        self.problems.add('file.py', 10, 'Tabs bad')
        self.assertEqual(1, len(self.problems))

        result = self.problems.all()
        expected = 'Tabs bad'
        self.assertEqual(expected, result[0].body)

    def test_add__with_diff_containing_block_offset(self):
        res = [
            PullFile(f, self.session) for f in json.loads(self.block_offset)
        ]
        changes = DiffCollection(res)

        problems = Problems(changes=changes)
        line_num = 32
        problems.add('somefile.py', line_num, 'Not good')
        self.assertEqual(1, len(problems))

        result = problems.all('somefile.py')
        first_result = result[0]
        self.assertIsInstance(first_result, Comment)
        self.assertEqual(
            changes.line_position('somefile.py', line_num),
            first_result.position,
            'Offset should be transformed to match value in changes'
        )

    def test_add_many(self):
        errors = [
            Comment('some/file.py', 10, 10, 'Thing is wrong'),
            Comment('some/file.py', 12, 12, 'Not good'),
        ]
        self.problems.add_many(errors)
        result = self.problems.all('some/file.py')
        self.assertEqual(2, len(result))
        self.assertEqual(errors, result)

    def test_limit_to_changes__remove_problems(self):
        res = [
            PullFile(f, self.session) for f in json.loads(self.two_files_json)
        ]
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
        self.assertEqual(2, len(result))
        expected = [
            Comment(filename_1, 117, 117, 'Something bad'),
            Comment(filename_1, 119, 119, 'Something else bad')]
        self.assertEqual(len(result), len(expected))
        self.assertEqual(result, expected)

        result = self.problems.all(filename_2)
        self.assertEqual(1, len(result))
        expected = [
            Comment(filename_2, 3, 3, 'Something bad')
        ]
        self.assertEqual(result, expected)

    def test_has_changes(self):
        problems = Problems(changes=None)
        self.assertFalse(problems.has_changes())

        problems = Problems(changes=[1])
        assert problems.has_changes()


def assert_review(test_case, call_args, errors, sha, body=''):
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
    test_case.assertEqual(actual.keys(), expected.keys())
    test_case.assertEqual(len(comments),
                          len(actual['comments']),
                          'Error and comment counts are off.')


def assert_checkrun(test_case, call_args, errors, run_id, body=''):
    """
    Check that the review comments match the error list.
    """
    test_case.assertEqual(run_id, call_args[0][0], 'Runid should match')

    actual = call_args[0][1]
    actual_annotations = actual['output']['annotations']
    expected = []
    for error in errors:
        value = {
            'message': error.body,
            'path': error.filename,
            'start_line': error.line,
            'end_line': error.line,
            'annotation_level': 'failure',
        }
        expected.append(value)

    test_case.assertEqual(len(expected), len(actual_annotations))
    for i, item in enumerate(expected):
        assert item == actual_annotations[i]

    conclusion = 'success' if len(expected) == 0 else 'failure'
    assert conclusion == actual['conclusion'], 'conclusion bad'
    assert actual['completed_at'], 'required field completed_at missing'
    assert actual['output']['title'], 'required field output.title missing'
    assert 'summary' in actual['output'], 'required field output.summary missing'
