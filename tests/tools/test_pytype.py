from lintreview.review import Problems, Comment
from lintreview.tools.pytype import Pytype
from unittest import TestCase
from tests import root_dir, requires_image, read_file, read_and_restore_file


class TestPytype(TestCase):

    fixtures = [
        'tests/fixtures/pytype/no_errors.py',
        'tests/fixtures/pytype/has_errors.py',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Pytype(self.problems, {}, root_dir)

    def test_version(self):
        assert self.tool.version != ''

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertTrue(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('dir/name/test.py'))

    @requires_image('pytype')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('pytype')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(3, len(problems))

        fname = self.fixtures[1]
        expected = Comment(
            fname, 6, 6,
            "No attribute 'group' on None [attribute-error]"
            " In Optional[Match[str]]")
        self.assertEqual(expected, problems[0])

        expected = Comment(
            fname, 9, 9, "Invalid __slot__ entry: '1' [bad-slots]")
        self.assertEqual(expected, problems[1])

    @requires_image('pytype')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        self.assertEqual([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(3, len(problems))

        fname = self.fixtures[1]
        expected = Comment(
            fname, 6, 6,
            "No attribute 'group' on None [attribute-error]"
            " In Optional[Match[str]]")
        self.assertEqual(expected, problems[0])

        expected = Comment(
            fname, 9, 9, "Invalid __slot__ entry: '1' [bad-slots]")
        self.assertEqual(expected, problems[1])

    @requires_image('pytype')
    def test_process_files__config_invalid(self):
        options = {
            'config': 'tests/fixtures/pytype/derp'
        }
        self.tool = Pytype(self.problems, options, root_dir)
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all()
        self.assertEqual(1, len(problems))
        self.assertIn('Pytype failed', problems[0].body)
        self.assertIn('config file', problems[0].body)

    @requires_image('pytype')
    def test_process_files__config(self):
        options = {
            'config': 'tests/fixtures/pytype/pytype.ini'
        }
        self.tool = Pytype(self.problems, options, root_dir)
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(2, len(problems))
        for p in problems:
            self.assertNotIn('attribute-error', p.body)

    def test_has_fixer(self):
        tool = Pytype(self.problems, {}, root_dir)
        self.assertEqual(False, tool.has_fixer())

    def test_has_fixer__enabled(self):
        tool = Pytype(self.problems, {'fixer': True}, root_dir)
        self.assertEqual(True, tool.has_fixer())

    @requires_image('pytype')
    def test_run_fixer(self):
        tool = Pytype(self.problems, {'fixer': True}, root_dir)

        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)

        updated = read_and_restore_file(self.fixtures[1], original)
        assert original != updated, 'File content should change.'
        self.assertEqual(0, len(self.problems.all()),
                         'No errors should be recorded')
