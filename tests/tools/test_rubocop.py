from __future__ import absolute_import
from unittest import TestCase

from lintreview.review import Comment, Problems
from lintreview.tools.rubocop import Rubocop
from tests import (
    root_dir, read_file, read_and_restore_file, requires_image
)


class TestRubocop(TestCase):

    fixtures = [
        'tests/fixtures/rubocop/no_errors.rb',
        'tests/fixtures/rubocop/has_errors.rb',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Rubocop(self.problems, {}, root_dir)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertTrue(self.tool.match_file('test.rb'))
        self.assertTrue(self.tool.match_file('dir/name/test.rb'))

    @requires_image('ruby2')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('ruby2')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])

        problems = self.problems.all(self.fixtures[1])
        expected = Comment(
            self.fixtures[1],
            4,
            4,
            'C: Trailing whitespace detected.')
        self.assertEqual(expected, problems[1])

    @requires_image('ruby2')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        linty_filename = self.fixtures[1]
        self.assertEqual(2, len(self.problems.all(linty_filename)))

        freshly_laundered_filename = self.fixtures[0]
        self.assertEqual([], self.problems.all(freshly_laundered_filename))

    @requires_image('ruby2')
    def test_process_files_one_file_fail_display_cop_names(self):
        options = {
            'display_cop_names': 'True',
        }
        self.tool = Rubocop(self.problems, options, root_dir)
        linty_filename = self.fixtures[1]
        self.tool.process_files([linty_filename])

        problems = self.problems.all(linty_filename)
        expected = Comment(
            linty_filename,
            4,
            4,
            'C: Layout/TrailingWhitespace: Trailing whitespace detected.')
        self.assertEqual(expected, problems[1])

    @requires_image('ruby2')
    def test_process_files_one_file_fail_display_cop_names__bool(self):
        options = {
            'display_cop_names': True,
        }
        self.tool = Rubocop(self.problems, options, root_dir)
        linty_filename = self.fixtures[1]
        self.tool.process_files([linty_filename])

        problems = self.problems.all(linty_filename)
        expected = Comment(
            linty_filename,
            4,
            4,
            'C: Layout/TrailingWhitespace: Trailing whitespace detected.')
        self.assertEqual(expected, problems[1])

    def test_has_fixer__not_enabled(self):
        tool = Rubocop(self.problems, {}, root_dir)
        self.assertEqual(False, tool.has_fixer())

    def test_has_fixer__enabled(self):
        tool = Rubocop(self.problems, {'fixer': True}, root_dir)
        self.assertEqual(True, tool.has_fixer())

    @requires_image('ruby2')
    def test_execute_fixer(self):
        tool = Rubocop(self.problems, {'fixer': True}, root_dir)

        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)

        updated = read_and_restore_file(self.fixtures[1], original)
        assert original != updated, 'File content should change.'
        self.assertEqual(0, len(self.problems.all()),
                         'No errors should be recorded')

    @requires_image('ruby2')
    def test_execute_fixer__fewer_problems_remain(self):
        tool = Rubocop(self.problems, {'fixer': True}, root_dir)

        # The fixture file can have all problems fixed by rubocop
        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)
        tool.process_files(self.fixtures)

        read_and_restore_file(self.fixtures[1], original)
        self.assertEqual(1, len(self.problems.all()),
                         'Most errors should be fixed')
        self.assertIn('too long', self.problems.all()[0].body)
