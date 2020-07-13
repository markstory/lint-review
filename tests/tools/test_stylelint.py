from unittest import TestCase

from lintreview.review import Problems, Comment
from lintreview.tools.stylelint import Stylelint
from tests import requires_image, root_dir, read_file, read_and_restore_file


class TestStylelint(TestCase):

    fixtures = [
        'tests/fixtures/stylelint/no_errors.scss',
        'tests/fixtures/stylelint/has_errors.scss',
        'tests/fixtures/stylelint/has_more_errors.scss',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Stylelint(self.problems, base_path=root_dir)

    def test_version(self):
        assert self.tool.version != ''

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.sass'))
        self.assertTrue(self.tool.match_file('dir/name/test.sass'))
        self.assertTrue(self.tool.match_file('dir/name/test.scss'))
        self.assertTrue(self.tool.match_file('dir/name/test.less'))
        self.assertTrue(self.tool.match_file('dir/name/test.css'))

    @requires_image('nodejs')
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @requires_image('nodejs')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('nodejs')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(2, len(problems))

        fname = self.fixtures[1]
        error = ('Unexpected unknown at-rule "@include" '
                 '(at-rule-no-unknown) [error]')
        expected = Comment(fname, 2, 2, error)
        self.assertEqual(expected, problems[0])

    @requires_image('nodejs')
    def test_process_files__multiple_files(self):
        self.tool.process_files(self.fixtures)

        self.assertEqual([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(2, len(problems))

        problems = self.problems.all(self.fixtures[2])
        self.assertEqual(2, len(problems))

    @requires_image('nodejs')
    def test_process_files_with_config(self):
        config = {
            'config': 'tests/fixtures/stylelint/stylelintrc.json'
        }

        tool = Stylelint(self.problems, config, root_dir)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all()
        self.assertEqual(6, len(problems),
                         'Config file should change error count')

    @requires_image('nodejs')
    def test_process_files_with_invalid_config(self):
        config = {
            'config': 'tests/fixtures/stylelint/badconfig'
        }
        tool = Stylelint(self.problems, config, root_dir)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all()
        self.assertEqual(1, len(problems),
                         'Should capture missing config error')

        self.assertIn('Your configuration file', problems[0].body)
        self.assertIn('ENOENT', problems[0].body)

    @requires_image('nodejs')
    def test_process_files_with_bad_json(self):
        config = {
            'config': 'tests/fixtures/stylelint/invalid.json'
        }
        tool = Stylelint(self.problems, config, root_dir)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all()
        self.assertEqual(1, len(problems),
                         'Should capture missing config error')

        self.assertIn('Your configuration file', problems[0].body)
        self.assertIn('JSONError', problems[0].body)

    def test_has_fixer__not_enabled(self):
        tool = Stylelint(self.problems, {})
        self.assertEqual(False, tool.has_fixer())

    def test_has_fixer__enabled(self):
        tool = Stylelint(self.problems, {'fixer': True}, root_dir)
        self.assertEqual(True, tool.has_fixer())

    @requires_image('nodejs')
    def test_execute_fixer(self):
        fixture = self.fixtures[1]
        tool = Stylelint(self.problems, {
            'config': 'tests/fixtures/stylelint/stylelintrc.json',
            'fixer': True,
        }, root_dir)
        original = read_file(fixture)
        tool.execute_fixer([fixture])

        updated = read_and_restore_file(fixture, original)
        assert original != updated, 'File content should change.'
