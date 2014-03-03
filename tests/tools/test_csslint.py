from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.utils import in_path
from lintreview.utils import npm_exists
from lintreview.tools.csslint import Csslint
from unittest import TestCase
from unittest import skipIf
from nose.tools import eq_

csslint_missing = not(in_path('csslint') or npm_exists('csslint'))


class TestCsslint(TestCase):

    needs_csslint = skipIf(csslint_missing, 'Needs csslint')

    fixtures = [
        'tests/fixtures/csslint/no_errors.css',
        'tests/fixtures/csslint/has_errors.css',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Csslint(self.problems)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.css'))
        self.assertTrue(self.tool.match_file('dir/name/test.css'))

    @needs_csslint
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @needs_csslint
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @needs_csslint
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(2, len(problems))

        fname = self.fixtures[1]
        expected = Comment(fname, 1, 1, "Don't use IDs in selectors.")
        eq_(expected, problems[0])

        expected = Comment(
            fname,
            2,
            2,
            "Using width with padding can sometimes make elements larger than you expect.")
        eq_(expected, problems[1])

    @needs_csslint
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(2, len(problems))

    @needs_csslint
    def test_process_files_with_config(self):
        config = {
            'ignore': 'box-model'
        }
        tool = Csslint(self.problems, config)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all(self.fixtures[1])

        eq_(1, len(problems), 'Config file should lower error count.')

    @needs_csslint
    def test_process_files_with_config_from_evil_jerk(self):
        config = {
            'ignore': '`cat /etc/passwd`'
        }
        tool = Csslint(self.problems, config)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all(self.fixtures[1])
        assert len(problems) > 0, 'Shell injection fale'
