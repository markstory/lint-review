from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.tools.yamllint import Yamllint
from unittest import TestCase
from nose.tools import eq_


class TestYamllint(TestCase):

    fixtures = [
        'tests/fixtures/yamllint/no_errors.yaml',
        'tests/fixtures/yamllint/has_errors.yaml',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Yamllint(self.problems)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertTrue(self.tool.match_file('test.yaml'))
        self.assertTrue(self.tool.match_file('dir/name/test.yaml'))
        self.assertTrue(self.tool.match_file('test.yml'))
        self.assertTrue(self.tool.match_file('dir/name/test.yml'))

    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(5, len(problems))

        fname = self.fixtures[1]

        msg = "[warning] missing starting space in comment (comments)"
        expected = Comment(fname, 1, 1, msg)
        eq_(expected, problems[0])

        msg = ("[warning] missing document start \"---\" (document-start)\n"
               "[error] too many spaces inside braces (braces)")
        expected = Comment(fname, 2, 2, msg)
        eq_(expected, problems[1])

    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(5, len(problems))

        fname = self.fixtures[1]

        msg = "[warning] missing starting space in comment (comments)"
        expected = Comment(fname, 1, 1, msg)
        eq_(expected, problems[0])

        msg = ("[warning] missing document start \"---\" (document-start)\n"
               "[error] too many spaces inside braces (braces)")
        expected = Comment(fname, 2, 2, msg)
        eq_(expected, problems[1])
