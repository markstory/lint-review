from lintreview import web
from mock import patch, Mock
from nose.tools import eq_
from unittest import TestCase
import json

test_data = {
    'action': 'derp',
    'pull_request': {
        'number': '3',
        'head': {
            'ref': 'master',
            'repo': {
                'git_url': 'git://github.com/other/testing',
                'name': 'testing',
                'owner': {
                    'login': 'other',
                },
            },
        },
        'base': {
            'ref': 'master',
            'repo': {
                'name': 'testing',
                'git_url': 'git://github.com/mark/testing',
                'owner': {
                    'login': 'mark',
                },
            },
        },
    },
}


class WebTest(TestCase):

    def setUp(self):
        self.app = web.app.test_client()

    def test_ping(self):
        res = self.app.get('/ping')
        eq_("lint-review: %s pong\n" % (web.version,), res.data)

    def test_start_request_no_get(self):
        res = self.app.get('/review/start')
        eq_(405, res.status_code)

    def test_start_request_json_fail(self):
        data = {'herp': 'derp'}
        data = json.dumps(data)
        res = self.app.post('/review/start',
                            content_type='application/json', data=data)
        eq_(403, res.status_code)

    @patch('lintreview.web.process_pull_request')
    def test_start_request_unknown_action(self, task):
        data = json.dumps(test_data)
        res = self.app.post('/review/start',
                            content_type='application/json', data=data)
        eq_(204, res.status_code)
        eq_('', res.data)
        assert not(task.called)

    @patch('lintreview.web.get_lintrc')
    @patch('lintreview.web.process_pull_request')
    def test_start_request_fail_on_lint_rc_file(self, task, lintrc):
        lintrc.side_effect = IOError()

        data = json.dumps(test_data)
        self.app.post('/review/start',
                      content_type='application/json', data=data)
        assert not(task.called), 'No task should have been queued'

    @patch('lintreview.web.cleanup_pull_request')
    def test_start_review_closing_request(self, task):
        close = test_data.copy()
        close['action'] = 'closed'
        data = json.dumps(close)

        res = self.app.post('/review/start',
                            content_type='application/json', data=data)
        assert task.delay.called, 'Cleanup task should be scheduled'
        eq_(204, res.status_code)
        eq_('', res.data)

    @patch('lintreview.web.get_repository')
    @patch('lintreview.web.get_lintrc')
    @patch('lintreview.web.process_pull_request')
    def test_start_review_schedule_job(self, task, lintrc, get_repo):
        get_repo.return_value = Mock()

        opened = test_data.copy()
        opened['action'] = 'opened'
        data = json.dumps(opened)

        lintrc.return_value = """
[tools]
linters = pep8"""

        res = self.app.post('/review/start',
                            content_type='application/json', data=data)
        assert task.delay.called, 'Process request should be called'
        eq_(204, res.status_code)
        eq_('', res.data)

    @patch('lintreview.web.get_repository')
    @patch('lintreview.web.get_lintrc')
    @patch('lintreview.web.process_pull_request')
    def test_start_review_schedule_job__on_reopend(self, task, lintrc,
                                                   get_repo):
        get_repo.return_value = Mock()
        reopened = test_data.copy()
        reopened['action'] = 'reopened'
        data = json.dumps(reopened)

        lintrc.return_value = """
[tools]
linters = pep8"""

        res = self.app.post('/review/start',
                            content_type='application/json', data=data)
        assert task.delay.called, 'Process request should be called'
        eq_(204, res.status_code)
        eq_('', res.data)
