from unittest import TestCase

from lintreview.review import Comment, IssueComment, Problems
from lintreview.tools.tslint import Tslint
from tests import requires_image, root_dir

FILE_WITH_NO_ERRORS = 'tests/fixtures/tslint/no_errors.ts',
FILE_WITH_ERRORS = 'tests/fixtures/tslint/has_errors.ts'


class TestTslint(TestCase):

    def setUp(self):
        self.problems = Problems()
        options = {
            'config': 'tests/fixtures/tslint/tslint_good.json'
        }
        self.tool = Tslint(self.problems, options, root_dir)

    def test_version(self):
        assert self.tool.version != ''

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertTrue(self.tool.match_file('test.ts'))
        self.assertTrue(self.tool.match_file('test.tsx'))
        self.assertTrue(self.tool.match_file('dir/name/test.ts'))

    @requires_image('nodejs')
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @requires_image('nodejs')
    def test_process_files__pass(self):
        self.tool.process_files(FILE_WITH_NO_ERRORS)
        self.assertEqual([], self.problems.all(FILE_WITH_NO_ERRORS))

    @requires_image('nodejs')
    def test_process_files__fail(self):
        self.tool.process_files([FILE_WITH_ERRORS])
        problems = self.problems.all(FILE_WITH_ERRORS)
        self.assertEqual(3, len(problems))

        msg = ("Shadowed name: 'range'\n"
               "Spaces before function parens are disallowed")
        expected = Comment(FILE_WITH_ERRORS, 1, 1, msg)
        self.assertEqual(expected, problems[0])

    @requires_image('nodejs')
    def test_process_files__invalid_config(self):
        tool = Tslint(self.problems,
                      options={'config': 'invalid-file'},
                      base_path=root_dir)
        tool.process_files([FILE_WITH_ERRORS])
        problems = self.problems.all()
        self.assertEqual(1, len(problems), 'Invalid config returns 1 error')
        msg = ('Your tslint configuration file is missing or invalid. '
               'Please ensure that `invalid-file` exists and is valid JSON.')
        expected = [IssueComment(msg)]
        self.assertEqual(expected, problems)

    @requires_image('nodejs')
    def test_process_files__no_config_set_no_default(self):
        tool = Tslint(self.problems, options={}, base_path=root_dir)
        tool.process_files([FILE_WITH_ERRORS])
        problems = self.problems.all()
        self.assertEqual(1, len(problems), 'Missing config returns 1 error')
        msg = ('Your tslint configuration file is missing or invalid. '
               'Please ensure that `tslint.json` exists and is valid JSON.')
        expected = [IssueComment(msg)]
        self.assertEqual(expected, problems)

    @requires_image('nodejs')
    def test_process_files_with_config(self):
        options = {
            'config': 'tests/fixtures/tslint/tslint_good.json'
        }
        tool = Tslint(self.problems, options, root_dir)
        tool.process_files([FILE_WITH_ERRORS])

        problems = self.problems.all(FILE_WITH_ERRORS)

        msg = ("Shadowed name: 'range'\n"
               'Spaces before function parens are disallowed')
        expected = Comment(FILE_WITH_ERRORS, 1, 1, msg)
        self.assertEqual(expected, problems[0])

        msg = "The key 'middle' is not sorted alphabetically"
        expected = Comment(FILE_WITH_ERRORS, 11, 11, msg)
        self.assertEqual(expected, problems[1])

    @requires_image('nodejs')
    def test_process_files_with_project(self):
        options = {
            'project': 'tests/fixtures/tslint/tsconfig.json',
            'config': 'tests/fixtures/tslint/tslint_good.json'
        }
        tool = Tslint(self.problems, options, root_dir)
        tool.process_files([FILE_WITH_ERRORS])

        problems = self.problems.all(FILE_WITH_ERRORS)

        msg = ("Shadowed name: 'range'\n"
               'Spaces before function parens are disallowed')
        expected = Comment(FILE_WITH_ERRORS, 1, 1, msg)
        self.assertEqual(expected, problems[0])

        msg = "The key 'middle' is not sorted alphabetically"
        expected = Comment(FILE_WITH_ERRORS, 11, 11, msg)
        self.assertEqual(expected, problems[1])

    @requires_image('nodejs')
    def test_process_files__invalid_rule(self):
        options = {
            'config': 'tests/fixtures/tslint/tslint_invalid_rule.json'
        }
        tool = Tslint(self.problems, options, base_path=root_dir)
        tool.process_files([FILE_WITH_ERRORS])

        problems = self.problems.all()
        self.assertEqual(1, len(problems))
        msg = ('Your tslint configuration output the following error:\n'
               '```\n'
               'Could not find implementations for the following rules '
               'specified in the configuration:\n'
               '    not_a_real_rule\n'
               'Try upgrading TSLint and/or ensuring that you have all '
               'necessary custom rules installed.\n'
               'If TSLint was recently upgraded, you may '
               'have old rules configured which need to be cleaned up.\n'
               '```')
        expected = [IssueComment(msg)]
        self.assertEqual(expected, problems)

    @requires_image('nodejs')
    def test_process_files__warnings(self):
        options = {
            'config': 'tests/fixtures/tslint/tslint_warning_rule.json'
        }
        tool = Tslint(self.problems, options, base_path=root_dir)
        tool.process_files([FILE_WITH_ERRORS])

        problems = self.problems.all()
        self.assertEqual(4, len(problems))
        expected = (
            '`tslint` output the following warnings:\n'
            '\n'
            "* The 'no-boolean-literal-compare' rule requires type "
            "information."
        )
        self.assertEqual(expected, problems[0].body)
        self.assertIn("Shadowed name: 'range'", problems[1].body)

    @requires_image('nodejs')
    def test_process_files__unknown_module(self):
        options = {
            'config': 'tests/fixtures/tslint/tslint_missing_plugin.json'
        }
        tool = Tslint(self.problems, options, base_path=root_dir)
        tool.process_files([FILE_WITH_ERRORS])

        problems = self.problems.all()
        self.assertEqual(1, len(problems),
                         'Invalid config should report an error')

        error = problems[0]
        self.assertIn('Your tslint configuration output the following error:',
                      error.body)
        self.assertIn('Invalid "extends" configuration value', error.body)
        self.assertIn('could not require "tslint-lol"', error.body)
