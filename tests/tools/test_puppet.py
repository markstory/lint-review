from __future__ import absolute_import
from lintreview.review import Problems, Comment
from lintreview.tools.puppet import Puppet
from unittest import TestCase
from nose.tools import eq_
from operator import attrgetter
from tests import root_dir, requires_image


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
        ]

        problems = sorted(self.problems.all(filename), key=attrgetter('line'))
        eq_(expected_problems, problems)

    @requires_image('ruby2')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        linty_filename = self.fixtures[1]
        eq_(2, len(self.problems.all(linty_filename)))

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
