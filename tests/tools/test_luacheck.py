from __future__ import absolute_import
from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.tools.luacheck import Luacheck
from lintreview.utils import in_path
from unittest import TestCase
from unittest import skipIf
from nose.tools import eq_

luacheck_missing = not(in_path('luaCheck'))


class Testluacheck(TestCase):

    needs_luacheck = skipIf(luacheck_missing, 'Needs luacheck')

    fixtures = [
        'tests/fixtures/luacheck/no_errors.lua',
        'tests/fixtures/luacheck/has_errors.lua',
        'tests/fixtures/luacheck/has_warnings.lua',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Luacheck(self.problems)

    def test_match_file(self):
        self.assertTrue(self.tool.match_file('test.lua'))
        self.assertTrue(self.tool.match_file('dir/name/test.lua'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertFalse(self.tool.match_file('test.js'))

    @needs_luacheck
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @needs_luacheck
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @needs_luacheck
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(1, len(problems))

        fname = self.fixtures[1]
        expected = Comment(
            fname,
            5,
            5,
            '(E011) expected \'=\' near \'+\'')
        eq_(expected, problems[0])

    @needs_luacheck
    def test_process_files_three_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[2])
        eq_(2, len(problems))

        fname = self.fixtures[2]
        expected = Comment(
            fname,
            3,
            3,
            '(W213) unused loop variable \'a\'\n'
            '(W113) accessing undefined variable \'sometable\'')
        eq_(expected, problems[1])

    @needs_luacheck
    def test_process_files_with_config(self):
        config = {
            'config': 'tests/fixtures/luacheck/luacheckrc'
        }
        tool = Luacheck(self.problems, config)
        tool.process_files(self.fixtures)

        problems = self.problems.all(self.fixtures[2])
        eq_(1, len(problems), 'Config file should lower error count.')
