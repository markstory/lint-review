from __future__ import absolute_import
from . import load_fixture, fixer_ini, create_pull_files
from lintreview.config import build_review_config
from lintreview.diff import DiffCollection
from lintreview.processor import Processor
from lintreview.repo import GithubPullRequest
from github3.pulls import PullRequest
from mock import patch, sentinel, Mock, ANY
from nose.tools import eq_, raises
from unittest import TestCase
import os
import json


app_config = {
    'GITHUB_AUTHOR': 'bot <bot@example.com>',
    'SUMMARY_THRESHOLD': 50,
}


class ProcessorTest(TestCase):

    def get_pull_request(self):
        fixture = load_fixture('pull_request.json')
        model = PullRequest(json.loads(fixture)['pull_request'])

        files = load_fixture('one_file_pull_request.json')
        model.files = lambda: create_pull_files(files)

        return GithubPullRequest(model)

    def test_load_changes(self):
        pull = self.get_pull_request()
        repo = Mock()

        subject = Processor(repo, pull, './tests', app_config)
        subject.load_changes()

        eq_(1, len(subject._changes), 'File count is wrong')
        assert isinstance(subject._changes, DiffCollection)

    @raises(RuntimeError)
    def test_run_tools__no_changes(self):
        pull = self.get_pull_request()
        repo = Mock()

        subject = Processor(repo, pull, './tests', app_config)
        subject.run_tools(None)

    @patch('lintreview.processor.tools')
    @patch('lintreview.processor.fixers')
    def test_run_tools__ignore_patterns(self, fixer_stub, tool_stub):
        pull = self.get_pull_request()
        repo = Mock()

        config = build_review_config(fixer_ini)
        config.ignore_patterns = lambda: [
            'View/Helper/*']

        subject = Processor(repo, pull, './tests', app_config)
        subject.load_changes()
        subject.run_tools(config)
        tool_stub.run.assert_called_with(
            ANY,
            [],
            ANY)

    @patch('lintreview.processor.tools')
    @patch('lintreview.processor.fixers')
    def test_run_tools__execute_fixers(self, fixer_stub, tool_stub):
        pull = self.get_pull_request()
        repo = Mock()

        tool_stub.factory.return_value = sentinel.tools

        fixer_stub.create_context.return_value = sentinel.context
        fixer_stub.run_fixers.return_value = sentinel.diff

        config = build_review_config(fixer_ini)
        subject = Processor(repo, pull, './tests', app_config)
        subject.load_changes()
        subject.run_tools(config)

        file_path = './tests/View/Helper/AssetCompressHelper.php'
        fixer_stub.create_context.assert_called_with(
            config,
            app_config,
            './tests',
            pull.head_branch)
        fixer_stub.run_fixers.assert_called_with(
            sentinel.tools,
            './tests',
            [os.path.abspath(file_path)])
        fixer_stub.apply_fixer_diff.assert_called_with(
            subject._changes,
            sentinel.diff,
            sentinel.context)
        assert tool_stub.run.called, 'Should have ran'

    @patch('lintreview.processor.tools')
    @patch('lintreview.processor.fixers')
    def test_run_tools__execute_fixers_fail(self, fixer_stub, tool_stub):
        pull = self.get_pull_request()
        repo = Mock()

        tool_stub.factory.return_value = sentinel.tools

        fixer_stub.create_context.return_value = sentinel.context
        fixer_stub.run_fixers.side_effect = RuntimeError

        config = build_review_config(fixer_ini)
        subject = Processor(repo, pull, './tests', app_config)
        subject.load_changes()
        subject.run_tools(config)

        assert fixer_stub.create_context.called
        assert fixer_stub.run_fixers.called
        assert not fixer_stub.apply_fixer_diff.called
        assert tool_stub.run.called, 'Should have ran'

    def test_publish(self):
        pull = self.get_pull_request()
        repo = Mock()

        subject = Processor(repo, pull, './tests', app_config)
        subject._problems = Mock()
        subject._review = Mock()

        subject.publish()
        self.assertTrue(
            subject._problems.limit_to_changes.called,
            'Problems should be filtered.')
        self.assertTrue(
            subject._review.publish.called,
            'Review should be published.')
        subject._review.publish.assert_called_with(
            subject._problems, pull.head, 50)
