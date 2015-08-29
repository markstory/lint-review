from lintreview.review import Comment
from lintreview.review import Problems
from lintreview.tools.foodcritic import Foodcritic
from lintreview.utils import in_path
from unittest import TestCase, skipIf
from nose.tools import eq_


critic_missing = not(in_path('foodcritic'))


class TestFoodcritic(TestCase):
    needs_critic = skipIf(critic_missing, 'Missing foodcritic, cannot run')

    fixtures = [
        'tests/fixtures/foodcritic/noerrors',
        'tests/fixtures/foodcritic/errors',
    ]

    def setUp(self):
        self.problems = Problems()

    @needs_critic
    def test_process_cookbook_pass(self):
        self.tool = Foodcritic(self.problems, None, self.fixtures[0])
        self.tool.process_files(None)
        eq_([], self.problems.all())

    @needs_critic
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
