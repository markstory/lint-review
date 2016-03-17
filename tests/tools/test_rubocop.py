from os.path import abspath
from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.utils import in_path, bundle_exists
from lintreview.tools.rubocop import Rubocop
from unittest import TestCase
from unittest import skipIf
from nose.tools import eq_


rubocop_missing = not(in_path('rubocop') or bundle_exists('rubocop'))


class TestRubocop(TestCase):
    needs_rubocop = skipIf(rubocop_missing, 'Missing rubocop, cannot run')

    fixtures = [
        'tests/fixtures/rubocop/no_errors.rb',
        'tests/fixtures/rubocop/has_errors.rb',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Rubocop(self.problems)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertTrue(self.tool.match_file('test.rb'))
        self.assertTrue(self.tool.match_file('dir/name/test.rb'))

    @needs_rubocop
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @needs_rubocop
    def test_process_files__one_file_fail(self):
        linty_filename = abspath(self.fixtures[1])
        self.tool.process_files([linty_filename])

        problems = self.problems.all(linty_filename)
        expected = Comment(
            linty_filename,
            4,
            4,
            'C: Trailing whitespace detected.')
        eq_(expected, problems[1])

    @needs_rubocop
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        linty_filename = abspath(self.fixtures[1])
        eq_(2, len(self.problems.all(linty_filename)))

        freshly_laundered_filename = abspath(self.fixtures[0])
        eq_([], self.problems.all(freshly_laundered_filename))

    @needs_rubocop
    def test_process_files_one_file_fail_display_cop_names(self):
        options = {
            'display_cop_names': 'True',
        }
        self.tool = Rubocop(self.problems, options)
        linty_filename = abspath(self.fixtures[1])
        self.tool.process_files([linty_filename])

        problems = self.problems.all(linty_filename)
        expected = Comment(
            linty_filename,
            4,
            4,
            'C: Style/TrailingWhitespace: Trailing whitespace detected.')
        eq_(expected, problems[1])
