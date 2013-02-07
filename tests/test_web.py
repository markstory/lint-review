from lintreview import web
from mock import patch
from nose.tools import eq_
from unittest import TestCase
import json

test_data = {
    'action': 'derp',
    'pull_request': {
        'number': '3',
        'head': {
            'repo': {
                'git_url': 'testing',
            },
        },
        'base': {
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
        eq_("pong\n", res.data)

    def test_start_request_no_get(self):
        res = self.app.get('/review/start')
        eq_(405, res.status_code)

    def test_start_request_json_fail(self):
        data = {'herp': 'derp'}
        data = json.dumps(data)
        res = self.app.post('/review/start',
                content_type='application/json', data=data)
        eq_(403, res.status_code)

    @patch('lintreview.tasks.process_pull_request')
    def test_start_request_unknown_action(self, task):
        data = json.dumps(test_data)
        res = self.app.post('/review/start',
                content_type='application/json', data=data)
        eq_(204, res.status_code)
        eq_('', res.data)
        assert not(task.called)
