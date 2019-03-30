from __future__ import absolute_import
from tests import load_fixture, create_commits
from lintreview.review import Problems
from lintreview.review import IssueComment
from lintreview.tools.commitcheck import Commitcheck
from unittest import TestCase


class TestCommitCheck(TestCase):

    fixture = load_fixture('commits.json')

    def setUp(self):
        self.fixture_data = create_commits(self.fixture)
        self.problems = Problems()
        self.tool = Commitcheck(self.problems)

    def test_execute_commits__no_pattern(self):
        self.tool.options['pattern'] = ''
        self.tool.execute_commits(self.fixture_data)
        self.assertEqual(0, len(self.problems), 'Empty pattern does not find issues')

    def test_execute_commits__broken_regex(self):
        self.tool.options['pattern'] = '(.*'
        self.tool.execute_commits(self.fixture_data)
        self.assertEqual(0, len(self.problems), 'Empty pattern does not find issues')

    def test_execute_commits__match(self):
        self.tool.options['pattern'] = '\w+'
        self.tool.execute_commits(self.fixture_data)
        self.assertEqual(0, len(self.problems), 'Commits that do match are ok')

        self.tool.options['pattern'] = 'bugs?'
        self.tool.execute_commits(self.fixture_data)
        self.assertEqual(0, len(self.problems), 'Commits that do match are ok')

    def test_execute_commits__no_match(self):
        self.tool.options['pattern'] = '\d+'
        self.tool.execute_commits(self.fixture_data)
        self.assertEqual(1, len(self.problems), 'Commits that do not match cause errors')
        msg = (
            'The following commits had issues. '
            'The pattern \d+ was not found in:\n'
            '* 6dcb09b5b57875f334f61aebed695e2e4193db5e\n')
        expected = IssueComment(msg)
        self.assertEqual(expected, self.problems.all()[0])

    def test_execute_commits__custom_message(self):
        self.tool.options['pattern'] = '\d+'
        self.tool.options['message'] = 'You are bad.'
        self.tool.execute_commits(self.fixture_data)
        self.assertEqual(1, len(self.problems), 'Commits that do not match cause errors')
        msg = ('You are bad. The pattern \d+ was not found in:\n'
               '* 6dcb09b5b57875f334f61aebed695e2e4193db5e\n')
        expected = IssueComment(msg)
        self.assertEqual(expected, self.problems.all()[0])

    def test_execute_commits__ignore_author_email(self):
        self.tool.author = 'support@github.com'
        self.tool.options['pattern'] = '\d+'
        self.tool.execute_commits(self.fixture_data)
        self.assertEqual(0, len(self.problems))
