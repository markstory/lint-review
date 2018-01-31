from __future__ import absolute_import
from os.path import abspath
from lintreview.review import Comment, Problems
from lintreview.utils import in_path, bundle_exists
from lintreview.tools.rubocop import Rubocop
from tests import read_file, read_and_restore_file
from unittest import TestCase, skipIf
from nose.tools import eq_, assert_in


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
            'C: Layout/TrailingWhitespace: Trailing whitespace detected.')
        eq_(expected, problems[1])

    def test_has_fixer__not_enabled(self):
        tool = Rubocop(self.problems, {})
        eq_(False, tool.has_fixer())

    def test_has_fixer__enabled(self):
        tool = Rubocop(self.problems, {'fixer': True})
        eq_(True, tool.has_fixer())

    @needs_rubocop
    def test_execute_fixer(self):
        tool = Rubocop(self.problems, {'fixer': True})

        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)

        updated = read_and_restore_file(self.fixtures[1], original)
        assert original != updated, 'File content should change.'
        eq_(0, len(self.problems.all()), 'No errors should be recorded')

    @needs_rubocop
    def test_execute_fixer__fewer_problems_remain(self):
        tool = Rubocop(self.problems, {'fixer': True})

        # The fixture file can have all problems fixed by rubocop
        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)
        tool.process_files(self.fixtures)

        read_and_restore_file(self.fixtures[1], original)
        eq_(1, len(self.problems.all()), 'Most errors should be fixed')
        assert_in('too long', self.problems.all()[0].body)
