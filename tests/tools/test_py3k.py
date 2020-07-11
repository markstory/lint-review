from unittest import TestCase
from lintreview.review import Problems, Comment
from lintreview.tools.py3k import Py3k
from tests import root_dir, requires_image


class TestPy3k(TestCase):

    class fixtures:
        no_errors = 'tests/fixtures/py3k/no_errors.py'
        has_errors = 'tests/fixtures/py3k/has_errors.py'

    def setUp(self):
        self.problems = Problems()
        self.tool = Py3k(self.problems, base_path=root_dir)

    def test_version(self):
        assert self.tool.version != ''

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertTrue(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('dir/name/test.py'))

    @requires_image('python2')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures.no_errors])
        self.assertEqual([], self.problems.all(self.fixtures.no_errors))

    @requires_image('python2')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures.has_errors])
        problems = self.problems.all(self.fixtures.has_errors)
        self.assertEqual(2, len(problems))

        fname = self.fixtures.has_errors
        self.assertEqual([
            Comment(fname, 6, 6, 'E1601 print statement used'),
            Comment(fname, 11, 11,
                    'W1638 range built-in referenced when not iterating')
        ], problems)

    @requires_image('python2')
    def test_process_files__config_option_str(self):
        tool = Py3k(self.problems, {'ignore': 'W1638,E1601'}, root_dir)
        tool.process_files([self.fixtures.has_errors])
        problems = self.problems.all(self.fixtures.has_errors)
        self.assertEqual(0, len(problems))

    @requires_image('python2')
    def test_process_files__config_option_list(self):
        tool = Py3k(self.problems,
                    {'ignore': ['W1638', 'E1601']},
                    root_dir)
        tool.process_files([self.fixtures.has_errors])
        problems = self.problems.all(self.fixtures.has_errors)
        self.assertEqual(0, len(problems))

    @requires_image('python2')
    def test_process_files_two_files(self):
        self.tool.process_files([self.fixtures.no_errors,
                                 self.fixtures.has_errors])

        self.assertEqual([], self.problems.all(self.fixtures.no_errors))

        problems = self.problems.all(self.fixtures.has_errors)
        self.assertEqual(2, len(problems))

        fname = self.fixtures.has_errors
        self.assertEqual([
            Comment(fname, 6, 6, 'E1601 print statement used'),
            Comment(fname, 11, 11,
                    'W1638 range built-in referenced when not iterating')
        ], problems)

    @requires_image('python2')
    def test_process_files__ignore_patterns(self):
        tool = Py3k(self.problems,
                    {'ignore-patterns': ['has_err.*', 'no.*']},
                    root_dir)
        tool.process_files([self.fixtures.has_errors])
        problems = self.problems.all(self.fixtures.has_errors)
        self.assertEqual(0, len(problems))

    @requires_image('python2')
    def test_process_files__ignore_pattern_string(self):
        tool = Py3k(self.problems,
                    {'ignore-patterns': 'has.*,no_.*'},
                    root_dir)
        tool.process_files([self.fixtures.has_errors])
        problems = self.problems.all(self.fixtures.has_errors)
        self.assertEqual(0, len(problems))

    @requires_image('python2')
    def test_process_files__ignore_pattern_path(self):
        tool = Py3k(self.problems,
                    {'ignore-patterns': 'fixtures/py3k/.*'},
                    root_dir)
        tool.process_files([self.fixtures.has_errors])
        problems = self.problems.all(self.fixtures.has_errors)
        self.assertEqual(0, len(problems))

    @requires_image('python2')
    def test_process_files__ignore_pattern_miss(self):
        tool = Py3k(self.problems,
                    {'ignore-patterns': 'foo.*'},
                    root_dir)
        tool.process_files([self.fixtures.has_errors])
        problems = self.problems.all(self.fixtures.has_errors)
        self.assertEqual(2, len(problems))

    @requires_image('python2')
    def test_process_files__ignore_pattern_corrupt(self):
        tool = Py3k(self.problems,
                    {'ignore-patterns': '(foo'},
                    root_dir)
        tool.process_files([self.fixtures.has_errors])
        problems = self.problems.all(self.fixtures.has_errors)
        self.assertEqual(2, len(problems))
