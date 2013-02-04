from unittest import TestCase
from lintreview.review import Review
from nose.tools import eq_


class TestReview(TestCase):

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
