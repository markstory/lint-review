from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.tools.phpcs import Phpcs
from lintreview.utils import composer_exists
from unittest import TestCase
from unittest import skipIf
from nose.tools import eq_, ok_

phpcs_missing = not(composer_exists('phpcs'))


class Testphpcs(TestCase):

    needs_phpcs = skipIf(phpcs_missing, 'Needs phpcs')

    fixtures = [
        'tests/fixtures/phpcs/no_errors.php',
        'tests/fixtures/phpcs/has_errors.php',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Phpcs(self.problems)

    def test_match_file(self):
        self.assertTrue(self.tool.match_file('test.php'))
        self.assertTrue(self.tool.match_file('dir/name/test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertFalse(self.tool.match_file('test.js'))

    @needs_phpcs
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @needs_phpcs
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @needs_phpcs
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(3, len(problems))

        fname = self.fixtures[1]
        expected = Comment(
            fname,
            14,
            14,
            'Opening brace should be on a new line')
        eq_(expected, problems[0])

        expected = Comment(
            fname,
            16,
            16,
            "Spaces must be used to indent lines; tabs are not allowed")
        eq_(expected, problems[2])

    @needs_phpcs
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(3, len(problems))

    @needs_phpcs
    def test_process_files__with_config(self):
        config = {
            'standard': 'Zend'
        }
        tool = Phpcs(self.problems, config)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all(self.fixtures[1])

        eq_(3, len(problems), 'Changing standards changes error counts')

    @needs_phpcs
    def test_process_files__with_ignore(self):
        config = {
            'standard': 'PSR2',
            'ignore': 'tests/fixtures/phpcs/*'
        }
        tool = Phpcs(self.problems, config)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all(self.fixtures[1])

        eq_(0, len(problems), 'ignore option should exclude files')

    @needs_phpcs
    def test_process_files__with_exclude(self):
        config = {
            'standard': 'PSR2',
            'exclude': 'Generic.WhiteSpace.DisallowTabIndent'
        }
        tool = Phpcs(self.problems, config)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all(self.fixtures[1])

        eq_(1, len(problems), 'exclude option should reduce errors.')

    @needs_phpcs
    def test_process_files__with_invalid_exclude(self):
        config = {
            'standard': 'PSR2',
            'exclude': 'Derpity.Derp'
        }
        tool = Phpcs(self.problems, config)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all()
        eq_(1, len(problems), 'A failure comment should be logged.')

        error = problems[0].body
        ok_('Your PHPCS configuration output the following error' in error)
        ok_('Derpity.Derp' in error)

    def test_create_command__with_path_based_standard(self):
        command = 'vendor/bin/phpcs'
        if phpcs_missing:
            command = 'phpcs'
        config = {
            'standard': 'test/CodeStandards',
            'tab_width': 4,
        }
        tool = Phpcs(self.problems, config, '/some/path')
        result = tool.create_command(['some/file.php'])
        expected = [
            command,
            '--report=checkstyle',
            '--standard=/some/path/test/CodeStandards',
            '--extensions=php',
            '--tab-width=4',
            'some/file.php'
        ]
        eq_(result, expected)

    def test_create_command__ignore_option_as_list(self):
        config = {
            'standard': 'PSR2',
            'extensions': ['php', 'ctp'],
            'exclude': ['rule1', 'rule2'],
            'ignore': ['tests/fixtures/phpcs/*', 'tests/fixtures/eslint/*']
        }
        tool = Phpcs(self.problems, config)
        result = tool.create_command(['some/file.php'])
        command = 'vendor/bin/phpcs'
        if phpcs_missing:
            command = 'phpcs'
        expected = [
            command,
            '--report=checkstyle',
            '--standard=PSR2',
            '--ignore=tests/fixtures/phpcs/*,tests/fixtures/eslint/*',
            '--exclude=rule1,rule2',
            '--extensions=php,ctp',
            'some/file.php'
        ]
        eq_(result, expected)
