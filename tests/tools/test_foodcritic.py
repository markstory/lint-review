from lintreview.review import Comment
from lintreview.review import Problems
from lintreview.tools.foodcritic import Foodcritic
from unittest import TestCase
from nose.tools import eq_


class TestFoodcritic(TestCase):

    fixtures = [
        'tests/fixtures/foodcritic/noerrors',
        'tests/fixtures/foodcritic/errors',
    ]

    def setUp(self):
        self.problems = Problems()

    def test_process_cookbook_pass(self):
        self.tool = Foodcritic(self.problems, None, self.fixtures[0])
        self.tool.process_files(None)
        eq_([], self.problems.all())

    def test_process_cookbook_fail(self):
        self.tool = Foodcritic(self.problems, None, self.fixtures[1])
        self.tool.process_files(None)
        problems = self.problems.all()
        eq_(5, len(problems))

        expected = Comment(
            'tests/fixtures/foodcritic/errors/recipes/apache2.rb', 1, 1,
            'FC007: Ensure recipe dependencies are reflected in cookbook '
            'metadata')
        eq_(expected, problems[1])
