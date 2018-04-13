from __future__ import absolute_import
from lintreview.review import Problems, Comment
from lintreview.tools.puppet import Puppet
from unittest import TestCase
from nose.tools import eq_, assert_in
from operator import attrgetter
from tests import root_dir, requires_image, read_file, read_and_restore_file


class TestPuppet(TestCase):

    fixtures = [
        'tests/fixtures/puppet/no_errors.pp',
        'tests/fixtures/puppet/has_errors.pp',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Puppet(self.problems, {}, root_dir)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertTrue(self.tool.match_file('test.pp'))
        self.assertTrue(self.tool.match_file('dir/name/test.pp'))

    @requires_image('ruby2')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @requires_image('ruby2')
    def test_process_files__one_file_fail(self):
        filename = self.fixtures[1]
        self.tool.process_files([filename])
        expected_problems = [
            Comment(filename, 2, 2, 'ERROR:foo not in autoload module layout'),
            Comment(filename, 3, 3, 'ERROR:trailing whitespace found'),
            Comment(filename, 4, 4, 'WARNING:quoted boolean value found')
        ]

        problems = sorted(self.problems.all(filename), key=attrgetter('line'))
        eq_(expected_problems, problems)

    @requires_image('ruby2')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        linty_filename = self.fixtures[1]
        eq_(3, len(self.problems.all(linty_filename)))

        freshly_laundered_filename = self.fixtures[0]
        eq_([], self.problems.all(freshly_laundered_filename))

    @requires_image('ruby2')
    def test_process_files__with_config(self):
        config = {
            'config': 'tests/fixtures/puppet/puppetlint.rc'
        }
        tool = Puppet(self.problems, config)
        tool.process_files([self.fixtures[1]])

        eq_([], self.problems.all(self.fixtures[1]),
            'Config file should cause no errors on has_errors.pp')

    def test_has_fixer__not_enabled(self):
        tool = Puppet(self.problems, {}, root_dir)
        eq_(False, tool.has_fixer())

    def test_has_fixer__enabled(self):
        tool = Puppet(self.problems, {'fixer': True}, root_dir)
        eq_(True, tool.has_fixer())

    @requires_image('ruby2')
    def test_execute_fixer(self):
        tool = Puppet(self.problems, {'fixer': True}, root_dir)

        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)

        updated = read_and_restore_file(self.fixtures[1], original)
        assert original != updated, 'File content should change.'
        eq_(0, len(self.problems.all()), 'No errors should be recorded')

    @requires_image('ruby2')
    def test_execute_fixer__fewer_problems_remain(self):
        tool = Puppet(self.problems, {'fixer': True}, root_dir)

        # The fixture file should have fixable problems fixed
        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)
        tool.process_files(self.fixtures)

        read_and_restore_file(self.fixtures[1], original)
        eq_(1, len(self.problems.all()), 'Most errors should be fixed')
        assert_in('autoload module layout', self.problems.all()[0].body)

    @requires_image('ruby2')
    def test_execute_fixer__fixer_ignore(self):
        puppet_config = {
            'fixer': True,
            'fixer_ignore': 'quoted_booleans, variable_is_lowercase',
        }
        tool = Puppet(self.problems, puppet_config, root_dir)

        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)
        tool.process_files(self.fixtures)

        read_and_restore_file(self.fixtures[1], original)
        eq_(2, len(self.problems.all()), 'Most errors should be fixed')
        assert_in('autoload module layout', self.problems.all()[0].body)
        assert_in('quoted boolean', self.problems.all()[1].body)
