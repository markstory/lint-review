from . import load_fixture
from lintreview.processor import Processor
from lintreview.diff import DiffCollection
from mock import patch
from mock import Mock
from nose.tools import eq_
from nose.tools import raises
from pygithub3 import Github
from requests.models import Response
from unittest import TestCase

fixture_data = load_fixture('one_file_pull_request.json')


class ProcessorTest(TestCase):

    @patch('pygithub3.core.client.Client.get')
    def test_load_changes(self, http):
        gh = Github()
        response = Response()
        response._content = fixture_data
        http.return_value = response

        subject = Processor(gh, 1, '123abc', './tests')
        subject.load_changes()

        eq_(1, len(subject._changes), 'File count is wrong')
        assert isinstance(subject._changes, DiffCollection)

    @raises(RuntimeError)
    def test_run_tools__no_changes(self):
        subject = Processor(None, 1, '123abc', './tests')
        subject.run_tools(None)

    @patch('lintreview.processor.tools')
    def test_run_tools(self, tool_stub):
        stub = Mock()
        subject = Processor(None, 1, '123abc', './tests')
        subject._changes = Mock()
        subject.run_tools(stub)
        assert tool_stub.run.called, 'Should have ran'
        assert subject._changes.get_files.called, 'Should have been called'
        assert stub.ignore_patterns.called

    def test_publish(self):
        subject = Processor(None, 1, '123abc', './tests', {'SUMMARY_THRESHOLD': 50})
        subject._problems = Mock()
        subject._review = Mock()

        subject.publish()
        self.assertTrue(
            subject._problems.limit_to_changes.called,
            'Problems should be filtered.')
        self.assertTrue(
            subject._review.publish.called,
            'Review should be published.')
        subject._review.publish.assert_called_with(subject._problems, '123abc', 50)
