import json
from . import load_fixture
from lintreview.diff import DiffCollection
from lintreview.review import Review
from nose.tools import eq_
from unittest import TestCase


class TestReview(TestCase):

    two_files = json.loads(
        load_fixture('two_file_pull_request.json'))

    def setUp(self):
        self.review = Review({})

    def test_add_problems_with_base_path(self):
        review = Review({}, '/some/path/')
        review.add_problem('/some/path/file.py', (10, 'Not good'))
        eq_(None, review.problems('/some/path/file.py'))
        eq_(1, len(review.problems('file.py')))

    def test_add_problem(self):
        self.review.add_problem('some/file.py', (10, 'Thing is wrong'))
        self.review.add_problem('some/file.py', (12, 'Punctuation fail'))
        eq_(2, len(self.review.problems('some/file.py')))
        eq_(None, self.review.problems('does not exist.py'))

    def test_add_problems(self):
        problems = [
            (10, 'Thing is wrong'),
            (12, 'Not good'),
        ]
        self.review.add_problems('some/file.py', problems)
        result = self.review.problems('some/file.py')
        eq_(2, len(result))
        eq_(problems, result)

    def test_filter_problems__remove_problems(self):
        # Setup some fake problems.
        changes = DiffCollection(self.two_files)
        filename_1 = 'Console/Command/Task/AssetBuildTask.php'
        problems = (
            (117, 'Something bad'),
            (119, 'Something else bad'),
            (130, 'Filtered out, as line is not changed'),
        )
        self.review.add_problems(filename_1, problems)
        filename_2 = 'Test/test_files/View/Parse/single.ctp'
        problems = (
            (2, 'Filtered out'),
            (3, 'Something bad'),
            (7, 'Filtered out'),
        )
        self.review.add_problems(filename_2, problems)
        self.review.filter_problems(changes)

        result = self.review.problems(filename_1)
        eq_(2, len(result))
        expected = [(117, 'Something bad'), (119, 'Something else bad')]
        eq_(result, expected)

        result = self.review.problems(filename_2)
        eq_(1, len(result))
        expected = [(3, 'Something bad')]
        eq_(result, expected)
