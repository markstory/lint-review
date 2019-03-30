from __future__ import absolute_import
from unittest import TestCase

from lintreview.review import Problems, Comment
from lintreview.tools.shellcheck import Shellcheck
from tests import root_dir, requires_image


class Testshellcheck(TestCase):

    fixtures = [
        'tests/fixtures/shellcheck/no_errors.sh',
        'tests/fixtures/shellcheck/has_errors.sh',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Shellcheck(self.problems, {}, root_dir)

    def test_match_file(self):
        self.assertTrue(self.tool.match_file('test.bash'))
        self.assertTrue(self.tool.match_file('test.zsh'))
        self.assertTrue(self.tool.match_file('test.ksh'))
        self.assertTrue(self.tool.match_file('test.sh'))
        self.assertTrue(self.tool.match_file('dir/name/test.sh'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertFalse(self.tool.match_file('test.js'))

    def test_match_file__executable(self):
        res = self.tool.match_file('tests/fixtures/shellcheck/tool')
        self.assertTrue(res)

    @requires_image('shellcheck')
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @requires_image('shellcheck')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('shellcheck')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(3, len(problems))

        fname = self.fixtures[1]
        expected = Comment(
            fname,
            3,
            3,
            'a is referenced but not assigned.\nDouble quote to prevent '
            'globbing and word splitting.')
        self.assertEqual(expected, problems[0])

        expected = Comment(
            fname,
            4,
            4,
            'BASE appears unused. Verify it or export it.\n'
            'Use $(..) instead of legacy \`..\`.')
        self.assertEqual(expected, problems[1])

        expected = Comment(
            fname,
            6,
            6,
            ("The order of the 2>&1 and the redirect matters. "
             "The 2>&1 has to be last."))
        self.assertEqual(expected, problems[2])

    @requires_image('shellcheck')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        self.assertEqual([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(3, len(problems))

    @requires_image('shellcheck')
    def test_process_files_with_config(self):
        config = {
            'shell': 'bash',
            'exclude': 'SC2154,SC2069'
        }
        tool = Shellcheck(self.problems, config, root_dir)
        tool.process_files([self.fixtures[1]])

        problems = self.problems.all(self.fixtures[1])

        self.assertEqual(2, len(problems),
                         'Changing standards changes error counts')
