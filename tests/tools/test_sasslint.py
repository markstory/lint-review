from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.utils import in_path
from lintreview.utils import npm_exists
from lintreview.tools.sasslint import Sasslint
from unittest import TestCase
from unittest import skipIf
from nose.tools import eq_

sasslint_missing = not(in_path('sass-lint') or npm_exists('sass-lint'))


class TestSasslint(TestCase):

    needs_sasslint = skipIf(sasslint_missing, 'Needs sasslint')

    fixtures = [
        'tests/fixtures/sasslint/no_errors.scss',
        'tests/fixtures/sasslint/has_errors.scss',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Sasslint(self.problems)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.sass'))
        self.assertTrue(self.tool.match_file('dir/name/test.sass'))
        self.assertTrue(self.tool.match_file('dir/name/test.scss'))

    @needs_sasslint
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @needs_sasslint
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @needs_sasslint
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(1, len(problems))

        fname = self.fixtures[1]
        error = ("Mixins should come before declarations"
                 " (mixins-before-declarations)")
        expected = Comment(fname, 4, 4, error)
        eq_(expected, problems[0])

    @needs_sasslint
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(1, len(problems))

    @needs_sasslint
    def test_process_files_with_config_from_evil_jerk(self):
        config = {
            'ignore': '`cat /etc/passwd`'
        }
        tool = Sasslint(self.problems, config)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all(self.fixtures[1])
        assert len(problems) > 0, 'Shell injection fale'

    @needs_sasslint
    def test_process_files_with_config(self):
        config = {
            'config': 'tests/fixtures/sasslint/sass-lint.yml'
        }

        tool = Sasslint(self.problems, config)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all(self.fixtures[1])

        eq_(0, len(problems), 'Config file should lower error count.')
