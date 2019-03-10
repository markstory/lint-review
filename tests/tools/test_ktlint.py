from __future__ import absolute_import
from unittest import TestCase

from lintreview.review import Problems, Comment
from lintreview.tools.ktlint import Ktlint
from tests import (
    root_dir, requires_image, read_file, read_and_restore_file
)
from nose.tools import eq_


class TestKtlint(TestCase):

    fixtures = [
        'tests/fixtures/ktlint/no_errors.kt',
        'tests/fixtures/ktlint/has_errors.kt',
        'tests/fixtures/ktlint/android_has_errors.kt',
    ]

    def setUp(self):
        self.problems = Problems()
        options = {}
        self.tool = Ktlint(self.problems, options, root_dir)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.rb'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.kt'))
        self.assertTrue(self.tool.match_file('dir/name/test.kt'))
        self.assertTrue(self.tool.match_file('test.kts'))

    @requires_image('ktlint')
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @requires_image('ktlint')
    def test_process_files_pass(self):
        file_no_errors = self.fixtures[0]
        self.tool.process_files(file_no_errors)
        eq_([], self.problems.all(file_no_errors))

    @requires_image('ktlint')
    def test_process_files_fail(self):
        file_has_errors = self.fixtures[1]
        self.tool.process_files([file_has_errors])
        problems = self.problems.all(file_has_errors)
        eq_(2, len(problems))

        expected = Comment(file_has_errors, 1, 1, 'Redundant "toString()" call in string template')
        eq_(expected, problems[0])
        expected = Comment(file_has_errors, 2, 2, 'Redundant curly braces')
        eq_(expected, problems[1])

    @requires_image('ktlint')
    def test_process_files_with_android(self):
        file_android_has_errors = self.fixtures[2]
        tool = Ktlint(self.problems, {'android': True}, root_dir)
        tool.process_files([file_android_has_errors])
        problems = self.problems.all(file_android_has_errors)
        eq_(3, len(problems))

        expected = Comment(file_android_has_errors, 1, 1,
                           'class AndroidActivity should be declared in a file named AndroidActivity.kt '+
                           '(cannot be auto-corrected)')
        eq_(expected, problems[0])
        expected = Comment(file_android_has_errors, 9, 9,
                           'Wildcard import (cannot be auto-corrected)')
        eq_(expected, problems[1])
        # Android options should lint max line length in a file
        expected = Comment(file_android_has_errors, 51, 51,
                           'Exceeded max line length (100) (cannot be auto-corrected)')
        eq_(expected, problems[2])

    @requires_image('ktlint')
    def test_process_files_multiple_files(self):
        self.tool.process_files(self.fixtures)
        eq_([], self.problems.all(self.fixtures[0]))
        eq_(2, len(self.problems.all(self.fixtures[1])))
        # Without android options should only display 2 errors
        eq_(2, len(self.problems.all(self.fixtures[2])))

    def test_has_fixer__not_enabled(self):
        tool = Ktlint(self.problems, {}, root_dir)
        eq_(False, tool.has_fixer())

    def test_has_fixer__enabled(self):
        tool = Ktlint(self.problems, {'fixer': True}, root_dir)
        eq_(True, tool.has_fixer())

    @requires_image('ktlint')
    def test_process_files__with_ruleset(self):
        tool = Ktlint(self.problems, {'ruleset': '/path/to/custom/rulseset.jar'}, root_dir)
        eq_(['ktlint', '--color', '--reporter=checkstyle', '-R', '/path/to/custom/rulseset.jar'],
        tool._create_command())

    @requires_image('ktlint')
    def test_process_files__valid_config(self):
        editor_config = 'tests/fixtures/ktlint/.editorconfig'
        tool = Ktlint(self.problems, {'config': editor_config}, root_dir)
        eq_(['ktlint', '--color', '--reporter=checkstyle', '--editorconfig=', editor_config],
        tool._create_command())

    @requires_image('ktlint')
    def test_execute_fixer(self):
        tool = Ktlint(self.problems, {'fixer': True}, root_dir)
        target = root_dir + '/' + self.fixtures[1]
        original = read_file(target)
        tool.execute_fixer(self.fixtures)

        updated = read_and_restore_file(target, original)
        assert original != updated, 'File content should change.'
        eq_(0, len(self.problems.all()), 'No errors should be recorded')
