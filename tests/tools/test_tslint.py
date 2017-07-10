import os
from unittest import TestCase, skipIf
from lintreview.review import Problems
from lintreview.review import Comment, IssueComment
from lintreview.tools.tslint import Tslint
from lintreview.utils import in_path
from lintreview.utils import npm_exists
from nose.tools import eq_

tslint_missing = not(in_path('tslint') or npm_exists('tslint'))

FILE_WITH_NO_ERRORS = 'tests/fixtures/tslint/no_errors.ts',
FILE_WITH_ERRORS = 'tests/fixtures/tslint/has_errors.ts'


class TestTslint(TestCase):

    needs_tslint = skipIf(tslint_missing, 'Needs tslint to run')

    def setUp(self):
        self.problems = Problems()
        options = {
            'config': 'tests/fixtures/tslint/tslint_good.json'
        }
        self.tool = Tslint(self.problems, options)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertTrue(self.tool.match_file('test.ts'))
        self.assertTrue(self.tool.match_file('dir/name/test.ts'))

    @needs_tslint
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @needs_tslint
    def test_process_files__pass(self):
        self.tool.process_files(FILE_WITH_NO_ERRORS)
        eq_([], self.problems.all(FILE_WITH_NO_ERRORS))

    @needs_tslint
    def test_process_files__fail(self):
        self.tool.process_files([FILE_WITH_ERRORS])
        problems = self.problems.all(FILE_WITH_ERRORS)
        eq_(3, len(problems))

        msg = ("Shadowed name: 'range'\n"
               "Spaces before function parens are disallowed")
        expected = Comment(FILE_WITH_ERRORS, 1, 1, msg)
        eq_(expected, problems[0])

    @needs_tslint
    def test_process_files__invalid_config(self):
        tool = Tslint(self.problems, options={'config': 'invalid-file'})
        tool.process_files([FILE_WITH_ERRORS])
        problems = self.problems.all()
        eq_(1, len(problems), 'Invalid config returns 1 error')
        msg = ('Your tslint config file is missing or invalid. '
               'Please ensure that `invalid-file` exists and is valid JSON.')
        expected = [IssueComment(msg)]
        eq_(expected, problems)

    @needs_tslint
    def test_process_files__no_config_set_no_default(self):
        tool = Tslint(self.problems, options={})
        tool.process_files([FILE_WITH_ERRORS])
        problems = self.problems.all()
        eq_(1, len(problems), 'Missing config returns 1 error')
        msg = ('Your tslint config file is missing or invalid. '
               'Please ensure that `tslint.json` exists and is valid JSON.')
        expected = [IssueComment(msg)]
        eq_(expected, problems)

    @needs_tslint
    def test_process_files_with_config(self):
        options = {
            'config': 'tests/fixtures/tslint/tslint_good.json'
        }
        tool = Tslint(self.problems, options)
        tool.process_files([FILE_WITH_ERRORS])

        problems = self.problems.all(FILE_WITH_ERRORS)

        msg = ("Shadowed name: 'range'\n"
               'Spaces before function parens are disallowed')
        expected = Comment(FILE_WITH_ERRORS, 1, 1, msg)
        eq_(expected, problems[0])

        msg = "The key 'middle' is not sorted alphabetically"
        expected = Comment(FILE_WITH_ERRORS, 11, 11, msg)
        eq_(expected, problems[1])

    @needs_tslint
    def test_process_output__ancestor_directory(self):
        # Simulate XML with ../file in the output
        # which happens with tslint
        options = {
            'config': 'tests/fixtures/tslint/tslint_good.json'
        }
        restore = os.getcwd()
        tool = Tslint(self.problems, options, restore)
        xml = """<?xml version="1.0" encoding="utf-8"?>
<checkstyle version="4.3">
  <file name="../tests/fixtures/tslint/has_errors.ts">
    <error line="11" column="3" severity="error" message="bad code"
      source="failure.tslint.object-literal-sort-keys" />
  </file>
</checkstyle>"""
        os.chdir(os.path.join('.', 'lintreview'))
        tool._process_output(xml, [FILE_WITH_ERRORS])
        os.chdir(restore)

        problems = self.problems.all(FILE_WITH_ERRORS)
        expected = Comment(FILE_WITH_ERRORS, 11, 11, 'bad code')
        eq_(expected, problems[0])

    @needs_tslint
    def test_process_files__invalid_rule(self):
        options = {
            'config': 'tests/fixtures/tslint/tslint_invalid_rule.json'
        }
        tool = Tslint(self.problems, options)
        tool.process_files([FILE_WITH_ERRORS])

        problems = self.problems.all()
        eq_(1, len(problems))
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
        eq_(expected, problems)
