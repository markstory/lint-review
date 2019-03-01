from __future__ import absolute_import
from lintreview.review import Problems, Comment
from lintreview.tools.stylelint import Stylelint
from unittest import TestCase
from nose.tools import eq_, assert_in
from tests import root_dir, requires_image


class TestStylelint(TestCase):

    fixtures = [
        'tests/fixtures/stylelint/no_errors.scss',
        'tests/fixtures/stylelint/has_errors.scss',
        'tests/fixtures/stylelint/has_more_errors.scss',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Stylelint(self.problems, base_path=root_dir)

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
        eq_([], self.problems.all(self.fixtures[0]))

    @requires_image('nodejs')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(2, len(problems))

        fname = self.fixtures[1]
        error = 'Unexpected unknown at-rule "@include" (at-rule-no-unknown) [error]'
        expected = Comment(fname, 6, 6, error)
        eq_(expected, problems[0])

    @requires_image('nodejs')
    def test_process_files__multiple_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(2, len(problems))

        problems = self.problems.all(self.fixtures[2])
        eq_(2, len(problems))

    @requires_image('nodejs')
    def test_process_files_with_config(self):
        config = {
            'config': 'tests/fixtures/stylelint/stylelintrc.json'
        }

        tool = Stylelint(self.problems, config, root_dir)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all()
        eq_(3, len(problems), 'Config file should change error count')

    @requires_image('nodejs')
    def test_process_files_with_invalid_config(self):
        config = {
            'config': 'tests/fixtures/stylelint/badconfig'
        }
        tool = Stylelint(self.problems, config, root_dir)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all()
        eq_(1, len(problems), 'Should capture missing config error')

        assert_in('Your configuration file', problems[0].body)
        assert_in('ENOENT', problems[0].body)
