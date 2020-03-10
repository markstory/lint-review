import json
import responses

from tests import load_fixture, temp_env
from unittest import TestCase


class TestParseArgs(TestCase):

    def _do_parse(self, args):
        # force config regeneration between tests

        from lintreview.cli import parse_args
        from lintreview.config import load_config
        import lintreview.web as web

        web.config = load_config()
        web.app.config.update(web.config)

        parse_args(args)

    @responses.activate
    def test_can_create_repo_webhook_via_cli(self):
        responses.add(
            responses.GET,
            'https://api.github.com/repos/markstory/lint-test',
            json=json.loads(load_fixture('repository.json')),
            status=200
        )

        # no hooks exist
        responses.add(
            responses.GET,
            'https://api.github.com/repos/markstory/lint-test/hooks?per_page=100',
            json=[],
            status=200
        )

        # allow for hook creation
        responses.add(
            responses.POST,
            'https://api.github.com/repos/markstory/lint-test/hooks',
            json=json.loads(load_fixture('webhook_list.json'))[0],
            status=201
        )

        mock_env = {
            'LINTREVIEW_SETTINGS': 'settings.sample.py',
            'LINTREVIEW_SERVER_NAME': 'example.com'
        }

        with temp_env(mock_env):
            self._do_parse(['register', '--user', 'cool-token', 'markstory', 'lint-test'])

        webhook_creation_request = responses.calls[2].request

        self.assertEqual(webhook_creation_request.headers['Authorization'], 'token cool-token')
        self.assertEqual(webhook_creation_request.url, 'https://api.github.com/repos/markstory/lint-test/hooks')
        self.assertEqual(webhook_creation_request.method, responses.POST)
        self.assertEqual(
            json.loads(webhook_creation_request.body),
            {
                "name": "web",
                "config": {
                    "url": "http://example.com/review/start",
                    "content_type": "json"
                },
                "events": ["pull_request"],
                "active": True
            }
        )

    @responses.activate
    def test_create_repo_webhook_does_nothing_if_webhook_already_exists(self):
        responses.add(
            responses.GET,
            'https://api.github.com/repos/markstory/lint-test',
            json=json.loads(load_fixture('repository.json')),
            status=200
        )

        # hook already exists
        responses.add(
            responses.GET,
            'https://api.github.com/repos/markstory/lint-test/hooks?per_page=100',
            json=json.loads(load_fixture('webhook_list.json')),
            status=200
        )

        mock_env = {
            'LINTREVIEW_SETTINGS': 'settings.sample.py',
            'LINTREVIEW_SERVER_NAME': 'example.com'
        }

        with temp_env(mock_env):
            self._do_parse(['register', '--user', 'cool-token', 'markstory', 'lint-test'])

        for request_call in responses.calls:
            self.assertNotEqual(request_call.request.method, responses.POST)

    @responses.activate
    def test_remove_repo_webhook_sends_correct_request_if_webhook_exists(self):
        responses.add(
            responses.GET,
            'https://api.github.com/repos/markstory/lint-test',
            json=json.loads(load_fixture('repository.json')),
            status=200
        )

        webhook_list_json = json.loads(load_fixture('webhook_list.json'))

        # hook exists
        responses.add(
            responses.GET,
            'https://api.github.com/repos/markstory/lint-test/hooks?per_page=100',
            json=webhook_list_json,
            status=200
        )

        responses.add(
            responses.GET,
            'https://api.github.com/repos/markstory/lint-test/hooks/706986',
            json=webhook_list_json[0],
            status=200
        )

        responses.add(
            responses.DELETE,
            'https://api.github.com/repos/markstory/lint-test/hooks/706986',
            status=204
        )

        mock_env = {
            'LINTREVIEW_SETTINGS': 'settings.sample.py',
            'LINTREVIEW_SERVER_NAME': 'example.com'
        }

        with temp_env(mock_env):
            self._do_parse(['unregister', '--user', 'cool-token', 'markstory', 'lint-test'])

        webhook_deletion_request = responses.calls[3].request

        self.assertEqual(webhook_deletion_request.headers['Authorization'], 'token cool-token')
        self.assertEqual(webhook_deletion_request.url, 'https://api.github.com/repos/markstory/lint-test/hooks/706986')
        self.assertEqual(webhook_deletion_request.method, responses.DELETE)

    @responses.activate
    def test_remove_repo_webhook_blows_up_if_webhook_does_not_exist(self):
        responses.add(
            responses.GET,
            'https://api.github.com/repos/markstory/lint-test',
            json=json.loads(load_fixture('repository.json')),
            status=200
        )

        # hook does not exist
        responses.add(
            responses.GET,
            'https://api.github.com/repos/markstory/lint-test/hooks?per_page=100',
            json=[],
            status=200
        )

        mock_env = {
            'LINTREVIEW_SETTINGS': 'settings.sample.py',
            'LINTREVIEW_SERVER_NAME': 'example.com'
        }

        with temp_env(mock_env):
            with self.assertRaises(SystemExit):
                self._do_parse(['unregister', '--user', 'cool-token', 'markstory', 'lint-test'])

    @responses.activate
    def test_can_create_org_webhook_via_cli(self):
        responses.add(
            responses.GET,
            'https://api.github.com/orgs/github',
            json=json.loads(load_fixture('organization.json')),
            status=200
        )

        # no hooks exist
        responses.add(
            responses.GET,
            'https://api.github.com/orgs/github/hooks?per_page=100',
            json=[],
            status=200
        )

        # allow for hook creation
        responses.add(
            responses.POST,
            'https://api.github.com/orgs/github/hooks',
            json=json.loads(load_fixture('org_webhook_list.json'))[0],
            status=201
        )

        mock_env = {
            'LINTREVIEW_SETTINGS': 'settings.sample.py',
            'LINTREVIEW_SERVER_NAME': 'example.com'
        }

        with temp_env(mock_env):
            self._do_parse(['org-register', '--user', 'cool-token', 'github'])

        webhook_creation_request = responses.calls[2].request

        self.assertEqual(webhook_creation_request.headers['Authorization'], 'token cool-token')
        self.assertEqual(webhook_creation_request.url, 'https://api.github.com/orgs/github/hooks')
        self.assertEqual(webhook_creation_request.method, responses.POST)
        self.assertEqual(
            json.loads(webhook_creation_request.body),
            {
                "name": "web",
                "config": {
                    "url": "http://example.com/review/start",
                    "content_type": "json"
                },
                "events": ["pull_request"],
                "active": True
            }
        )

    @responses.activate
    def test_create_org_webhook_does_nothing_if_webhook_already_exists(self):
        responses.add(
            responses.GET,
            'https://api.github.com/orgs/github',
            json=json.loads(load_fixture('organization.json')),
            status=200
        )

        # hook already exists
        responses.add(
            responses.GET,
            'https://api.github.com/orgs/github/hooks?per_page=100',
            json=json.loads(load_fixture('org_webhook_list.json')),
            status=200
        )

        mock_env = {
            'LINTREVIEW_SETTINGS': 'settings.sample.py',
            'LINTREVIEW_SERVER_NAME': 'example.com'
        }

        with temp_env(mock_env):
            self._do_parse(['org-register', '--user', 'cool-token', 'github'])

        for request_call in responses.calls:
            self.assertNotEqual(request_call.request.method, responses.POST)

    @responses.activate
    def test_remove_org_webhook_sends_correct_request_if_webhook_exists(self):
        responses.add(
            responses.GET,
            'https://api.github.com/orgs/github',
            json=json.loads(load_fixture('organization.json')),
            status=200
        )

        webhook_list_json = json.loads(load_fixture('org_webhook_list.json'))

        # hook exists
        responses.add(
            responses.GET,
            'https://api.github.com/orgs/github/hooks?per_page=100',
            json=webhook_list_json,
            status=200
        )

        responses.add(
            responses.GET,
            'https://api.github.com/orgs/github/hooks/706986',
            json=webhook_list_json[0],
            status=200
        )

        responses.add(
            responses.DELETE,
            'https://api.github.com/orgs/github/hooks/706986',
            status=204
        )

        mock_env = {
            'LINTREVIEW_SETTINGS': 'settings.sample.py',
            'LINTREVIEW_SERVER_NAME': 'example.com'
        }

        with temp_env(mock_env):
            self._do_parse(['org-unregister', '--user', 'cool-token', 'github'])

        webhook_deletion_request = responses.calls[3].request

        self.assertEqual(webhook_deletion_request.headers['Authorization'], 'token cool-token')
        self.assertEqual(webhook_deletion_request.url, 'https://api.github.com/orgs/github/hooks/706986')
        self.assertEqual(webhook_deletion_request.method, responses.DELETE)

    @responses.activate
    def test_remove_org_webhook_blows_up_if_webhook_does_not_exist(self):
        responses.add(
            responses.GET,
            'https://api.github.com/orgs/github',
            json=json.loads(load_fixture('organization.json')),
            status=200
        )

        # hook does not exist
        responses.add(
            responses.GET,
            'https://api.github.com/orgs/github/hooks?per_page=100',
            json=[],
            status=200
        )

        mock_env = {
            'LINTREVIEW_SETTINGS': 'settings.sample.py',
            'LINTREVIEW_SERVER_NAME': 'example.com'
        }

        with temp_env(mock_env):
            with self.assertRaises(SystemExit):
                self._do_parse(['org-unregister', '--user', 'cool-token', 'github'])
