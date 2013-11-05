from . import load_fixture
from lintreview.diff import DiffCollection
from lintreview.review import Review
from lintreview.review import Problems
from lintreview.review import Comment
from mock import patch
from mock import Mock
from mock import call
from nose.tools import eq_
from pygithub3 import Github
from pygithub3.resources.base import Resource
from requests.models import Response
from unittest import TestCase


class TestReview(TestCase):

    def setUp(self):
        self.review = Review({}, 2)

    @patch('pygithub3.core.client.Client.get')
    def test_load_comments__none_active(self, http):
        fixture_data = load_fixture('comments_none_current.json')
        response = Response()
        response._content = fixture_data
        http.return_value = response

        gh = Github()
        review = Review(gh, 2)
        review.load_comments()

        eq_(0, len(review.comments("View/Helper/AssetCompressHelper.php")))

    @patch('pygithub3.core.client.Client.get')
    def test_load_comments__loads_comments(self, http):
        fixture_data = load_fixture('comments_current.json')
        response = Response()
        response._content = fixture_data
        http.return_value = response

        gh = Github()
        review = Review(gh, 2)
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

    @patch('pygithub3.core.client.Client.get')
    def test_filter_existing__removes_duplicates(self, http):
        fixture_data = load_fixture('comments_current.json')
        response = Response()
        response._content = fixture_data
        http.return_value = response

        gh = Github()
        problems = Problems()
        review = Review(gh, 2)
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
        gh = Mock()
        problems = Problems()

        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
            (filename_1, 117, 'Something bad'),
            (filename_1, 119, 'Something bad'),
        )
        problems.add_many(errors)
        sha = 'abc123'

        review = Review(gh, 3)
        review.publish_problems(problems, sha)

        assert gh.pull_requests.comments.create.called
        eq_(2, gh.pull_requests.comments.create.call_count)
        calls = gh.pull_requests.comments.create.call_args_list

        expected = call(3, {
            'commit_id': sha,
            'path': errors[0][0],
            'position': errors[0][1],
            'body': errors[0][2]
        })
        eq_(calls[0], expected)

        expected = call(3, {
            'commit_id': sha,
            'path': errors[1][0],
            'position': errors[1][1],
            'body': errors[1][2]
        })
        eq_(calls[1], expected)

    def test_publish_ok_comment(self):
        gh = Mock()
        problems = Problems(changes=[1])
        review = Review(gh, 3)

        sha = 'abc123'
        review.publish(problems, sha)

        assert not(gh.pull_requests.comments.create.called)
        assert gh.issues.comments.create.called

        calls = gh.issues.comments.create.call_args_list

        expected = call(3, ':+1: No lint errors found.')
        eq_(calls[0], expected)

    def test_publish_empty_comment(self):
        gh = Mock()
        problems = Problems(changes=[])
        review = Review(gh, 3)

        sha = 'abc123'
        review.publish(problems, sha)

        assert not(gh.pull_requests.comments.create.called)
        assert gh.issues.comments.create.called

        calls = gh.issues.comments.create.call_args_list

        msg = ('Could not review pull request. '
               'It may be too large, or contain no reviewable changes.')
        expected = call(3, msg)
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
        res = Resource.loads(self.block_offset)
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
        res = Resource.loads(self.two_files_json)
        changes = DiffCollection(res)

        # Setup some fake problems.
        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        errors = (
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
            (filename_1, 117, 'Something bad'),
            (filename_1, 119, 'Something else bad')]
        eq_(result.sort(), expected.sort())

        result = self.problems.all(filename_2)
        eq_(1, len(result))
        expected = [Comment(filename_2, 3, 3, 'Something bad')]
        eq_(result, expected)

    def test_has_changes(self):
        problems = Problems(changes=None)
        self.assertFalse(problems.has_changes())

        problems = Problems(changes=[1])
        assert problems.has_changes()
