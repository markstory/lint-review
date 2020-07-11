from lintreview.review import Problems
from lintreview.tools.black import Black
from unittest import TestCase
from tests import root_dir, read_file, read_and_restore_file, requires_image


class TestBlack(TestCase):

    fixtures = [
        'tests/fixtures/black/no_errors.py',
        'tests/fixtures/black/has_errors.py',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Black(self.problems, {}, root_dir)

    def test_version(self):
        assert self.tool.version != ''

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertTrue(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('dir/name/test.py'))

    @requires_image('python3')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('python3')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all()

        self.assertEqual(1, len(problems))
        self.assertIn('* ' + self.fixtures[1], problems[0].body)

    @requires_image('python3')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        problems = self.problems.all()
        self.assertEqual(1, len(problems))

        self.assertIn('do not match the `black` styleguide', problems[0].body)
        self.assertIn('* ' + self.fixtures[1], problems[0].body)
        self.assertNotIn(self.fixtures[0], problems[0].body)

    @requires_image('python3')
    def test_process_absolute_container_path(self):
        fixtures = ['/src/' + path for path in self.fixtures]
        self.tool.process_files(fixtures)

        self.assertEqual(1, len(self.problems.all()))

    @requires_image('python3')
    def test_process_files__config(self):
        options = {
            'config': 'tests/fixtures/black/pyproject.toml'
        }
        self.tool = Black(self.problems, options, root_dir)
        self.tool.process_files([self.fixtures[1]])

        problems = self.problems.all()
        self.assertEqual(1, len(problems))
        self.assertIn(self.fixtures[1], problems[0].body)

    def test_has_fixer__not_enabled(self):
        tool = Black(self.problems, {})
        self.assertEqual(False, tool.has_fixer())

    def test_has_fixer__enabled(self):
        tool = Black(self.problems, {'fixer': True})
        self.assertEqual(True, tool.has_fixer())

    @requires_image('python3')
    def test_execute_fixer(self):
        tool = Black(self.problems, {'fixer': True}, root_dir)

        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)
        tool.process_files(self.fixtures)

        updated = read_and_restore_file(self.fixtures[1], original)
        assert original != updated, 'File content should change.'
        self.assertEqual(0, len(self.problems.all()),
                         'No errors should be recorded')
