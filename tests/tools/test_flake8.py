from __future__ import absolute_import
from lintreview.review import Problems
from lintreview.tools.flake8 import Flake8
from unittest import TestCase
from tests import requires_image, root_dir, read_file, read_and_restore_file


class TestFlake8(TestCase):

    fixtures = [
        'tests/fixtures/flake8/no_errors.py',
        'tests/fixtures/flake8/has_errors.py',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Flake8(self.problems, {}, root_dir)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertTrue(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('dir/name/test.py'))

    @requires_image('python2')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('python2')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        assert len(problems) >= 6

        self.assertEqual(7, problems[0].line)
        self.assertEqual(7, problems[0].position)
        self.assertIn('multiple imports on one line', problems[0].body)

    @requires_image('python2')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        self.assertEqual([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        assert len(problems) >= 6

        self.assertEqual(7, problems[0].line)
        self.assertEqual(7, problems[0].position)
        self.assertIn('multiple imports on one line', problems[0].body)

    @requires_image('python2')
    def test_process_absolute_container_path(self):
        fixtures = ['/src/' + path for path in self.fixtures]
        self.tool.process_files(fixtures)

        self.assertEqual([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        assert len(problems) >= 6

        self.assertEqual(7, problems[0].line)
        self.assertEqual(7, problems[0].position)
        self.assertIn('multiple imports on one line', problems[0].body)

    @requires_image('python2')
    def test_execute_config_with_format(self):
        tool = Flake8(
            self.problems,
            {'config': 'tests/fixtures/pep8/flake8_bad_format.ini'},
            root_dir)
        fixtures = ['/src/' + path for path in self.fixtures]
        tool.process_files(fixtures)
        problems = self.problems.all(self.fixtures[1])
        assert len(problems), 'should have problems'
        for issue in problems:
            assert 'W302' not in issue.body

    @requires_image('python2')
    def test_process_files_two_files__python3(self):
        self.tool.options['python'] = 3
        self.tool.process_files(self.fixtures)

        self.assertEqual([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        assert len(problems) >= 6

        self.assertEqual(7, problems[0].line)
        self.assertEqual(7, problems[0].position)
        self.assertIn('multiple imports on one line', problems[0].body)

    @requires_image('python2')
    def test_config_options_and_process_file(self):
        options = {
            'ignore': 'F4,W603',
        }
        self.tool = Flake8(self.problems, options, root_dir)
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        assert len(problems) >= 5
        for p in problems:
            self.assertFalse('F4' in p.body)
            self.assertFalse('W603' in p.body)

    def test_make_command__no_config(self):
        options = {
            'ignore': 'F4,W603',
            'max-line-length': 120,
            'max-complexity': 10
        }
        tool = Flake8(self.problems, options, root_dir)
        out = tool.make_command([self.fixtures[1]])
        expected = [
            'flake8',
            '--ignore', 'F4,W603',
            '--max-complexity', 10,
            '--max-line-length', 120,
            '--isolated',
            self.fixtures[1]
        ]
        self.assertEqual(set(expected), set(out))

    def test_make_command__config(self):
        options = {
            'ignore': 'F4,W603',
            'max-line-length': 120,
            'max-complexity': 10,
            'config': '.flake8'
        }
        tool = Flake8(self.problems, options, root_dir)
        out = tool.make_command([self.fixtures[1]])
        expected = [
            'flake8',
            '--ignore', 'F4,W603',
            '--max-complexity', 10,
            '--max-line-length', 120,
            '--config', '/src/.flake8',
            '--format', 'default',
            self.fixtures[1]
        ]
        self.assertEqual(set(expected), set(out))

    def test_has_fixer__not_enabled(self):
        tool = Flake8(self.problems, {}, root_dir)
        self.assertEqual(False, tool.has_fixer())

    def test_has_fixer__enabled(self):
        tool = Flake8(self.problems, {'fixer': True}, root_dir)
        self.assertEqual(True, tool.has_fixer())

    @requires_image('python2')
    def test_execute_fixer(self):
        tool = Flake8(self.problems, {'fixer': True}, root_dir)

        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)

        updated = read_and_restore_file(self.fixtures[1], original)
        assert original != updated, 'File content should change.'
        self.assertEqual(0, len(self.problems.all()),
                         'No errors should be recorded')

    @requires_image('python2')
    def test_execute_fixer__fewer_problems_remain(self):
        tool = Flake8(self.problems, {'fixer': True}, root_dir)

        # The fixture file can have all problems fixed by autopep8
        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)
        tool.process_files(self.fixtures)

        read_and_restore_file(self.fixtures[1], original)
        assert 1 < len(self.problems.all()), 'Most errors should be fixed'

        text = [c.body for c in self.problems.all()]
        self.assertIn("'<>' is deprecated", ' '.join(text))

    @requires_image('python2')
    def test_execute_fixer__python3(self):
        options = {'fixer': True, 'python': 3}
        tool = Flake8(self.problems, options, root_dir)

        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)

        updated = read_and_restore_file(self.fixtures[1], original)
        assert original != updated, 'File content should change.'
        self.assertEqual(0, len(self.problems.all()),
                         'No errors should be recorded')

    @requires_image('python2')
    def test_execute_fixer__fewer_problems_remain__python3(self):
        options = {'fixer': True, 'python': 3}
        tool = Flake8(self.problems, options, root_dir)

        # The fixture file can have all problems fixed by autopep8
        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)
        tool.process_files(self.fixtures)

        read_and_restore_file(self.fixtures[1], original)
        self.assertGreaterEqual(len(self.problems.all()), 1,
                                'Most errors should be fixed')

        text = [c.body for c in self.problems.all()]
        self.assertIn("'<>' is deprecated", ' '.join(text))
