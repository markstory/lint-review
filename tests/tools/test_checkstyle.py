from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.tools.checkstyle import Checkstyle
from lintreview.utils import in_path
from unittest import TestCase
from unittest import skipIf
from nose.tools import eq_, assert_in

checkstyle_missing = not(in_path('checkstyle'))


class TestCheckstyle(TestCase):

    needs_checkstyle = skipIf(checkstyle_missing, 'Needs checkstyle to run')

    fixtures = [
        'tests/fixtures/checkstyle/no_errors.java',
        'tests/fixtures/checkstyle/has_errors.java',
    ]

    def setUp(self):
        self.problems = Problems()
        config = {
            'config': 'tests/fixtures/checkstyle/config.xml'
        }
        self.tool = Checkstyle(self.problems, config)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.java'))
        self.assertTrue(self.tool.match_file('dir/name/test.java'))

    @needs_checkstyle
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @needs_checkstyle
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @needs_checkstyle
    def test_process_files__multiple_error(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(4, len(problems))

        fname = self.fixtures[1]

        expected = Comment(
            fname,
            1,
            1,
            "Missing a Javadoc comment.\n"
            "Utility classes should not have a public or default constructor.")
        eq_(expected, problems[0])

        expected = Comment(
            fname,
            3,
            3,
            "Missing a Javadoc comment.\n"
            "Parameter args should be final."
        )
        eq_(expected, problems[2])

    @needs_checkstyle
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(4, len(problems))

    @needs_checkstyle
    def test_process_files__no_config_comment(self):
        config = {}
        tool = Checkstyle(self.problems, config)
        tool.process_files(self.fixtures)

        problems = self.problems.all()
        eq_(1, len(problems))
        assert_in('could not run `checkstyle`', problems[0].body)

    @needs_checkstyle
    def test_process_files__missing_config(self):
        config = {'config': 'badness.xml'}
        tool = Checkstyle(self.problems, config)
        tool.process_files(self.fixtures)

        problems = self.problems.all()
        eq_(1, len(problems))
        assert_in('Running `checkstyle` failed', problems[0].body)
        assert_in('config file exists and is valid XML', problems[0].body)

    def test_create_command__with_path_based_standard(self):
        config = {
            'config': 'test/checkstyle.xml'
        }
        tool = Checkstyle(self.problems, config, '/some/path')
        result = tool.create_command(['some/file.js'])
        expected = [
            'checkstyle',
            '-f', 'xml',
            '-c', '/some/path/test/checkstyle.xml',
            'some/file.js'
        ]
        assert 'checkstyle' in result[0], 'checkstyle is in command name'
        eq_(result, expected)
