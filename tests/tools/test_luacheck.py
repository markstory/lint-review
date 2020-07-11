from lintreview.review import Problems, Comment
from lintreview.tools.luacheck import Luacheck
from unittest import TestCase
from tests import root_dir, requires_image


class Testluacheck(TestCase):

    fixtures = [
        'tests/fixtures/luacheck/no_errors.lua',
        'tests/fixtures/luacheck/has_errors.lua',
        'tests/fixtures/luacheck/has_warnings.lua',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Luacheck(self.problems, {}, root_dir)

    def test_version(self):
        assert self.tool.version != ''

    def test_match_file(self):
        self.assertTrue(self.tool.match_file('test.lua'))
        self.assertTrue(self.tool.match_file('dir/name/test.lua'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertFalse(self.tool.match_file('test.js'))

    @requires_image('luacheck')
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @requires_image('luacheck')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('luacheck')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(1, len(problems))

        fname = self.fixtures[1]
        expected = Comment(
            fname,
            5,
            5,
            '(E011) expected \'=\' near \'+\'')
        self.assertEqual(expected, problems[0])

    @requires_image('luacheck')
    def test_process_files_three_files(self):
        self.tool.process_files(self.fixtures)

        self.assertEqual([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[2])
        self.assertEqual(2, len(problems))

        fname = self.fixtures[2]
        expected = Comment(
            fname,
            3,
            3,
            '(W213) unused loop variable \'a\'\n'
            '(W113) accessing undefined variable \'sometable\'')
        self.assertEqual(expected, problems[1])

    @requires_image('luacheck')
    def test_process_files_with_config(self):
        config = {
            'config': 'tests/fixtures/luacheck/luacheckrc'
        }
        tool = Luacheck(self.problems, config, root_dir)
        tool.process_files(self.fixtures)

        problems = self.problems.all(self.fixtures[2])
        self.assertEqual(1, len(problems),
                         'Config file should lower error count.')

    @requires_image('luacheck')
    def test_process_files_with_missing_config(self):
        config = {
            'config': 'not_a_file'
        }
        tool = Luacheck(self.problems, config, root_dir)
        tool.process_files(self.fixtures)

        problems = self.problems.all()
        self.assertEqual(1, len(problems),
                         "Couldn't load configuration from")
        self.assertIn("Couldn't", problems[0].body)
        self.assertIn("configuration", problems[0].body)
        self.assertIn("not_a_file", problems[0].body)
