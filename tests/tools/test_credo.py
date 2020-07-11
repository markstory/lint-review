from lintreview.review import Comment, Problems
from lintreview.tools.credo import Credo
from unittest import TestCase
from tests import root_dir, requires_image


class TestCredo(TestCase):

    fixtures = [
        'tests/fixtures/credo/no_errors.ex',
        'tests/fixtures/credo/has_errors.ex',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Credo(self.problems, {}, root_dir)

    def test_version(self):
        assert self.tool.version != ''

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertTrue(self.tool.match_file('test.ex'))
        self.assertTrue(self.tool.match_file('test.exs'))
        self.assertTrue(self.tool.match_file('dir/name/test.ex'))
        self.assertTrue(self.tool.match_file('dir/name/test.exs'))

    def test_create_command_types(self):
        self.tool.options = {
            'all': True,
            'all-priorities': 'yes',
            'strict': 1,
        }
        command = self.tool.create_command()
        self.assertTrue('--all' in command)
        self.assertTrue('--all-priorities' in command)
        self.assertTrue('--strict' in command)

    @requires_image('credo')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('credo')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(1, len(problems))
        fname = self.fixtures[1]
        expected = Comment(fname, 1, 1,
                           'Modules should have a @moduledoc tag.')
        self.assertEqual(expected, problems[0])
