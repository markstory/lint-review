from unittest import TestCase

from lintreview.review import Problems, Comment
from lintreview.tools.yamllint import Yamllint
from tests import root_dir, requires_image


class TestYamllint(TestCase):

    fixtures = [
        'tests/fixtures/yamllint/no_errors.yaml',
        'tests/fixtures/yamllint/has_errors.yaml',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Yamllint(self.problems, {}, root_dir)

    def test_version(self):
        assert self.tool.version != ''

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertTrue(self.tool.match_file('test.yaml'))
        self.assertTrue(self.tool.match_file('dir/name/test.yaml'))
        self.assertTrue(self.tool.match_file('test.yml'))
        self.assertTrue(self.tool.match_file('dir/name/test.yml'))

    @requires_image('python2')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('python2')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(5, len(problems))

        fname = self.fixtures[1]

        msg = "[warning] missing starting space in comment (comments)"
        expected = Comment(fname, 1, 1, msg)
        self.assertEqual(expected, problems[0])

        msg = ("[warning] missing document start \"---\" (document-start)\n"
               "[error] too many spaces inside braces (braces)")
        expected = Comment(fname, 2, 2, msg)
        self.assertEqual(expected, problems[1])

    @requires_image('python2')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        self.assertEqual([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(5, len(problems))

        fname = self.fixtures[1]

        msg = "[warning] missing starting space in comment (comments)"
        expected = Comment(fname, 1, 1, msg)
        self.assertEqual(expected, problems[0])

        msg = ("[warning] missing document start \"---\" (document-start)\n"
               "[error] too many spaces inside braces (braces)")
        expected = Comment(fname, 2, 2, msg)
        self.assertEqual(expected, problems[1])

    @requires_image('python2')
    def test_process_files__config(self):
        config = {
            'config': 'tests/fixtures/yamllint/config.yaml'
        }
        tool = Yamllint(self.problems, config, root_dir)
        tool.process_files([self.fixtures[0]])

        problems = self.problems.all(self.fixtures[0])

        self.assertEqual(1, len(problems),
                         'Config file should cause errors on no_errors.yml')

    @requires_image('python2')
    def test_process_files__missing_config(self):
        config = {
            'config': 'tests/fixtures/yamllint/lol.yaml'
        }
        tool = Yamllint(self.problems, config, root_dir)
        tool.process_files([self.fixtures[0]])

        problems = self.problems.all()

        self.assertEqual(1, len(problems))
        self.assertIn(
            '`yamllint` failed with the following error:\n'
            '```\n'
            "IOError: [Errno 2] No such file or directory: "
            "'/src/tests/fixtures/yamllint/lol.yaml'\n"
            '```\n',
            problems[0].body)
