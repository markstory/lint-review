from unittest import TestCase

from lintreview.review import Problems, Comment
from lintreview.tools.sasslint import Sasslint
from tests import root_dir, requires_image


class TestSasslint(TestCase):

    fixtures = [
        'tests/fixtures/sasslint/no_errors.scss',
        'tests/fixtures/sasslint/has_errors.scss',
        'tests/fixtures/sasslint/has_more_errors.scss',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Sasslint(self.problems, base_path=root_dir)

    def test_version(self):
        assert self.tool.version != ''

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.sass'))
        self.assertTrue(self.tool.match_file('dir/name/test.sass'))
        self.assertTrue(self.tool.match_file('dir/name/test.scss'))

    @requires_image('nodejs')
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @requires_image('nodejs')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('nodejs')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(1, len(problems))

        fname = self.fixtures[1]
        error = ("Mixins should come before declarations "
                 "(mixins-before-declarations)")
        expected = Comment(fname, 4, 4, error)
        self.assertEqual(expected, problems[0])

    @requires_image('nodejs')
    def test_process_files__multiple_files(self):
        self.tool.process_files(self.fixtures)

        self.assertEqual([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(1, len(problems))

        problems = self.problems.all(self.fixtures[2])
        self.assertEqual(1, len(problems))

    @requires_image('nodejs')
    def test_process_files_with_config_from_evil_jerk(self):
        config = {
            'ignore': '`cat /etc/passwd`'
        }
        tool = Sasslint(self.problems, config, root_dir)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all(self.fixtures[1])
        assert len(problems) > 0, 'Shell injection fale'

    @requires_image('nodejs')
    def test_process_files_with_config(self):
        config = {
            'config': 'tests/fixtures/sasslint/sass-lint.yml'
        }

        tool = Sasslint(self.problems, config, root_dir)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all(self.fixtures[1])

        self.assertEqual(0, len(problems),
                         'Config file should lower error count.')
