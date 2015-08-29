from os.path import abspath
from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.utils import in_path, bundle_exists
from lintreview.tools.puppet import Puppet
from unittest import TestCase
from unittest import skipIf
from nose.tools import eq_
from operator import attrgetter

puppet_missing = not(in_path('puppet-lint') or bundle_exists('puppet-lint'))


class TestPuppet(TestCase):
    needs_puppet = skipIf(puppet_missing, 'Missing puppet-lint, cannot run')

    fixtures = [
        'tests/fixtures/puppet/no_errors.pp',
        'tests/fixtures/puppet/has_errors.pp',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Puppet(self.problems)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertTrue(self.tool.match_file('test.pp'))
        self.assertTrue(self.tool.match_file('dir/name/test.pp'))

    @needs_puppet
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @needs_puppet
    def test_process_files__one_file_fail(self):
        filename = abspath(self.fixtures[1])
        self.tool.process_files([filename])
        expected_problems = [
            Comment(filename, 2, 2, 'ERROR:foo not in autoload module layout'),
            Comment(filename, 3, 3, 'ERROR:trailing whitespace found'),
        ]

        problems = sorted(self.problems.all(filename), key=attrgetter('line'))
        eq_(expected_problems, problems)

    @needs_puppet
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        linty_filename = abspath(self.fixtures[1])
        eq_(2, len(self.problems.all(linty_filename)))

        freshly_laundered_filename = abspath(self.fixtures[0])
        eq_([], self.problems.all(freshly_laundered_filename))
