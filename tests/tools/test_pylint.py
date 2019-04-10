from __future__ import absolute_import

from unittest import TestCase

from nose.tools import eq_
from tests import requires_image, root_dir

from lintreview.review import Comment, Problems
from lintreview.tools.pylint import Pylint


class TestPylint(TestCase):

    fixtures = [
        'tests/fixtures/pylint/no_errors.py',
        'tests/fixtures/pylint/has_errors.py',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Pylint(self.problems, {}, root_dir)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertTrue(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('dir/name/test.py'))

    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @requires_image('python2')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(7, len(problems))

        fname = self.fixtures[1]
        # pylint outputs are sorted by 'category', not line number
        eq_([
            Comment(fname, 6, 6, "C0330 Wrong continued indentation (add 17 spaces)."),
            Comment(fname, 12, 12, "C0326 Exactly one space required around assignment"),
            Comment(fname, 1, 1, "C0111 Missing module docstring"),
            Comment(fname, 2, 2, "C0410 Multiple imports on one line (os, re)\n"
                    "W0611 Unused import re\nW0611 Unused import os"),
            Comment(fname, 4, 4, "C0111 Missing function docstring\nW0613 Unused argument 'self'"),
            Comment(fname, 5, 5, "E1120 No value for argument 'arg3' in function call"),
            Comment(fname, 9, 9, "W0613 Unused argument 'arg3'")
        ], problems)

    @requires_image('python2')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(7, len(problems))
        expected = Comment(self.fixtures[1], 6, 6,
                           "C0330 Wrong continued indentation (add 17 spaces).")
        eq_(expected, problems[0])

    @requires_image('python3')
    def test_process_files_two_files__python3(self):
        self.tool.options['python'] = 3
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(7, len(problems))
        expected = Comment(self.fixtures[1], 6, 6,
                           "C0330 Wrong continued indentation (add 17 spaces).")
        eq_(expected, problems[0])

    @requires_image('python2')
    def test_process_absolute_container_path(self):
        fixtures = ['/src/' + path for path in self.fixtures]
        self.tool.process_files(fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        assert len(problems) >= 6

    @requires_image('python2')
    def test_process_files__disable(self):
        options = {
            'disable': 'C,W0611,E1120',
        }
        self.tool = Pylint(self.problems, options, root_dir)
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_([
            Comment(self.fixtures[1], 4, 4, "W0613 Unused argument 'self'"),
            Comment(self.fixtures[1], 9, 9, "W0613 Unused argument 'arg3'"),
        ], problems)

    @requires_image('python2')
    def test_process_files__enable(self):
        options = {
            'disable': 'C,W,E',
            'enable': 'W0613',
        }
        self.tool = Pylint(self.problems, options, root_dir)
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_([
            Comment(self.fixtures[1], 4, 4, "W0613 Unused argument 'self'"),
            Comment(self.fixtures[1], 9, 9, "W0613 Unused argument 'arg3'"),
        ], problems)

    @requires_image('python2')
    def test_process_files__config(self):
        options = {
            'config': 'tests/fixtures/pylint/sample_rcfile',
        }
        self.tool = Pylint(self.problems, options, root_dir)
        filename = self.fixtures[1]
        self.tool.process_files([filename])
        problems = self.problems.all(self.fixtures[1])
        eq_([
            Comment(filename, 10, 10, "C0301 Line too long (51/50)"),
            Comment(filename, 1, 1, "C0302 Too many lines in module (16/3)"),
            Comment(filename, 9, 9, "R0913 Too many arguments (3/1)"),
            Comment(filename, 15, 15, "C1901 Avoid comparisons to empty string"),
        ], problems)
