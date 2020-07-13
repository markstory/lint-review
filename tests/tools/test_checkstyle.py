from lintreview.review import Problems, Comment
from lintreview.tools.checkstyle import Checkstyle
from unittest import TestCase
from tests import root_dir, requires_image


class TestCheckstyle(TestCase):

    fixtures = [
        'tests/fixtures/checkstyle/no_errors.java',
        'tests/fixtures/checkstyle/has_errors.java',
        'tests/fixtures/checkstyle/\u6c92\u6709\u932f\u8aa4.java',
    ]

    def setUp(self):
        self.problems = Problems()
        config = {
            'config': 'tests/fixtures/checkstyle/config.xml'
        }
        self.tool = Checkstyle(self.problems, config, root_dir)

    def test_version(self):
        assert self.tool.version != ''

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.java'))
        self.assertTrue(self.tool.match_file('dir/name/test.java'))

    @requires_image('checkstyle')
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @requires_image('checkstyle')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('checkstyle')
    def test_process_files__multiple_error(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(4, len(problems))

        fname = self.fixtures[1]

        expected = Comment(
            fname,
            1,
            1,
            "Utility classes should not have a public or default constructor.")
        self.assertEqual(expected, problems[0])

        expected = Comment(
            fname,
            3,
            3,
            "Parameter args should be final."
        )
        self.assertEqual(expected, problems[2])

    @requires_image('checkstyle')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        self.assertEqual([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(4, len(problems))

    @requires_image('checkstyle')
    def test_process_files__no_config_comment(self):
        config = {}
        tool = Checkstyle(self.problems, config)
        tool.process_files(self.fixtures)

        problems = self.problems.all()
        self.assertEqual(1, len(problems))
        self.assertIn('could not run `checkstyle`', problems[0].body)

    @requires_image('checkstyle')
    def test_process_files__missing_config(self):
        config = {'config': 'badness.xml'}
        tool = Checkstyle(self.problems, config, root_dir)
        tool.process_files(self.fixtures)

        problems = self.problems.all()
        self.assertEqual(1, len(problems))
        self.assertIn('Running `checkstyle` failed', problems[0].body)
        self.assertIn('config file exists and is valid XML', problems[0].body)

    def test_create_command__with_path_based_standard(self):
        config = {
            'config': 'test/checkstyle.xml'
        }
        tool = Checkstyle(self.problems, config, root_dir)
        result = tool.create_command('tmp1.properties', ['some/file.js'])
        expected = [
            'checkstyle',
            '-f', 'xml',
            '-p', '/src/tmp1.properties',
            '-c', '/src/test/checkstyle.xml',
            'some/file.js'
        ]
        assert 'checkstyle' in result[0], 'checkstyle is in command name'
        self.assertEqual(result, expected)
