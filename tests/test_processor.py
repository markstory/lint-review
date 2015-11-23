from . import load_fixture
from lintreview.processor import Processor
from lintreview.diff import DiffCollection
from github3.pulls import PullFile
from mock import patch
from mock import Mock
from nose.tools import eq_, raises
from unittest import TestCase
import json

fixture_data = load_fixture('one_file_pull_request.json')


class ProcessorTest(TestCase):

    def get_mock_client(self, fixture):
        gh = Mock()
        pull_request = Mock()

        pull_request.files.return_value = map(
            lambda f: PullFile(f),
            json.loads(fixture))

        gh.pull_request.return_value = pull_request
        return gh

    def test_load_changes(self):
        gh = self.get_mock_client(fixture_data)
        subject = Processor(gh, 1, '123abc', './tests')
        subject.load_changes()

        eq_(1, len(subject._changes), 'File count is wrong')
        assert isinstance(subject._changes, DiffCollection)

    @raises(RuntimeError)
    def test_run_tools__no_changes(self):
        gh = self.get_mock_client(fixture_data)

        subject = Processor(gh, 1, '123abc', './tests')
        subject.run_tools(None)

    @patch('lintreview.processor.tools')
    def test_run_tools(self, tool_stub):
        gh = self.get_mock_client(load_fixture('commits.json'))

        stub_config = Mock()
        subject = Processor(gh, 1, '123abc', './tests')
        subject._changes = Mock()
        subject.run_tools(stub_config)
        assert tool_stub.run.called, 'Should have ran'
        assert subject._changes.get_files.called, 'Should have been called'
        assert stub_config.ignore_patterns.called

    def test_publish(self):
        gh = self.get_mock_client(load_fixture('commits.json'))

        subject = Processor(gh, 1, '123abc', './tests', {'SUMMARY_THRESHOLD': 50})
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
            subject._problems, '123abc', 50)
