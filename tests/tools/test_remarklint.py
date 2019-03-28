from __future__ import absolute_import
from lintreview.review import Problems
from lintreview.tools.remarklint import Remarklint
from unittest import TestCase
from tests import root_dir, read_file, read_and_restore_file, requires_image


class TestRemarklint(TestCase):

    fixtures = [
        'tests/fixtures/remarklint/no_errors.md',
        'tests/fixtures/remarklint/has_errors.md',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Remarklint(self.problems, {}, root_dir)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.txt'))
        self.assertFalse(self.tool.match_file('test.rst'))
        self.assertFalse(self.tool.match_file('dir/name/test.rst'))
        self.assertTrue(self.tool.match_file('test.md'))
        self.assertTrue(self.tool.match_file('dir/name/test.md'))

    @requires_image('nodejs')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('nodejs')
    def test_process_files__one_file_file(self):
        self.tool.process_files([self.fixtures[1]])

        problems = self.problems.all()
        self.assertEqual(2, len(problems))
        self.assertIn('Incorrect list-item', problems[0].body)

    @requires_image('nodejs')
    def test_process_files__missing_plugin(self):
        tool = Remarklint(self.problems, {'fixer': True}, root_dir)

        config = 'tests/fixtures/remarklint/.remarkrc'
        original = read_file(config)
        with open(config, 'w') as f:
            f.write('{"plugins": ["unknown-preset"]}')
        tool.process_files([self.fixtures[1]])

        with open(config, 'w') as f:
            f.write(original)
        problems = self.problems.all()
        self.assertEqual(1, len(problems), 'Should have an error')
        self.assertIn('unknown-preset', problems[0].body)

    def test_process_files__config(self):
        pass

    def test_has_fixer__not_enabled(self):
        tool = Remarklint(self.problems)
        self.assertEqual(False, tool.has_fixer())

    def test_has_fixer__enabled(self):
        tool = Remarklint(self.problems, {'fixer': True})
        self.assertEqual(True, tool.has_fixer())

    @requires_image('nodejs')
    def test_execute_fixer(self):
        tool = Remarklint(self.problems, {'fixer': True}, root_dir)

        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)
        tool.process_files(self.fixtures)

        updated = read_and_restore_file(self.fixtures[1], original)
        assert original != updated, 'File content should change.'
        self.assertEqual(1, len(self.problems.all()),
                         'Fewer errors should be recorded')
