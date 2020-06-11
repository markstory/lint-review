from lintreview.review import Comment, Problems
from lintreview.tools.goodcheck import Goodcheck
from tests import (
    root_dir,
    requires_image,
)
from unittest import TestCase


class TestGoodcheck(TestCase):

    fixtures = [
        'tests/fixtures/goodcheck/no_errors.yml',
        'tests/fixtures/goodcheck/has_errors.yml',
    ]

    def setUp(self):
        self.problems = Problems()
        config = {
            'config': 'tests/fixtures/goodcheck/goodcheck.yml'
        }
        self.tool = Goodcheck(self.problems, config, root_dir)

    def test_match_file(self):
        self.assertTrue(self.tool.match_file('test.rb'))
        self.assertTrue(self.tool.match_file('dir/name/test.yaml'))

    @requires_image('ruby2')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('ruby2')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])

        problems = self.problems.all(self.fixtures[1])
        expected = Comment(
            self.fixtures[1],
            2,
            2,
            'Write "GitHub", not "Github"')
        self.assertEqual(expected, problems[0])

    @requires_image('ruby2')
    def test_process_files__two_files(self):
        self.tool.process_files(self.fixtures)

        linty_filename = self.fixtures[1]
        self.assertEqual(2, len(self.problems.all(linty_filename)))

        freshly_laundered_filename = self.fixtures[0]
        self.assertEqual([], self.problems.all(freshly_laundered_filename))

    @requires_image('ruby2')
    def test_process_specific_rules(self):
        options = {
            'rules': 'test.2, test.3',
            'config': 'tests/fixtures/goodcheck/goodcheck.yml'
        }
        self.tool = Goodcheck(self.problems, options, root_dir)
        self.tool.process_files([self.fixtures[1]])

        problems = self.problems.all(self.fixtures[1])
        expected = Comment(
            self.fixtures[1],
            3,
            3,
            'Use hostnames, not RFC 1918 IPs')
        self.assertEqual(expected, problems[0])

    @requires_image('ruby2')
    def test_add_justifications_to_comments(self):
        options = {
            'add_justifications_to_comments': True,
            'config': 'tests/fixtures/goodcheck/goodcheck.yml'
        }
        self.tool = Goodcheck(self.problems, options, root_dir)
        self.tool.process_files([self.fixtures[1]])

        problem_body = self.problems.all(self.fixtures[1])[1].body

        self.assertIn(" - Unless you can't find another way", problem_body)
        self.assertIn(" - some other reason", problem_body)
