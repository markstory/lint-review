from __future__ import absolute_import
from lintreview.review import Problems, Comment
from lintreview.tools.puppet import Puppet
from unittest import TestCase
from operator import attrgetter
from tests import requires_image, root_dir, read_file, read_and_restore_file


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
        self.assertEqual([], self.problems.all(self.fixtures[0]))

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
        self.assertEqual(expected_problems, problems)

    @requires_image('ruby2')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        linty_filename = self.fixtures[1]
        self.assertEqual(3, len(self.problems.all(linty_filename)))

        freshly_laundered_filename = self.fixtures[0]
        self.assertEqual([], self.problems.all(freshly_laundered_filename))

    @requires_image('ruby2')
    def test_process_files__with_config(self):
        config = {
            'config': 'tests/fixtures/puppet/puppetlint.rc'
        }
        tool = Puppet(self.problems, config)
        tool.process_files([self.fixtures[1]])

        self.assertEqual([], self.problems.all(self.fixtures[1]),
                         'Config file should cause no errors on has_errors.pp')

    def test_has_fixer__not_enabled(self):
        tool = Puppet(self.problems, {}, root_dir)
        self.assertEqual(False, tool.has_fixer())

    def test_has_fixer__enabled(self):
        tool = Puppet(self.problems, {'fixer': True}, root_dir)
        self.assertEqual(True, tool.has_fixer())

    @requires_image('ruby2')
    def test_execute_fixer(self):
        tool = Puppet(self.problems, {'fixer': True}, root_dir)

        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)

        updated = read_and_restore_file(self.fixtures[1], original)
        assert original != updated, 'File content should change.'
        self.assertEqual(0, len(self.problems.all()),
                         'No errors should be recorded')

    @requires_image('ruby2')
    def test_execute_fixer__fewer_problems_remain(self):
        tool = Puppet(self.problems, {'fixer': True}, root_dir)

        # The fixture file should have fixable problems fixed
        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)
        tool.process_files(self.fixtures)

        read_and_restore_file(self.fixtures[1], original)
        self.assertEqual(1, len(self.problems.all()),
                         'Most errors should be fixed')
        self.assertIn('autoload module layout', self.problems.all()[0].body)

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
        self.assertEqual(2, len(self.problems.all()),
                         'Most errors should be fixed')

        problems = sorted(self.problems.all(), key=attrgetter('line'))
        self.assertIn('ERROR:foo not in autoload module layout',
                      problems[0].body)
        self.assertIn('WARNING:quoted boolean value', problems[1].body)
