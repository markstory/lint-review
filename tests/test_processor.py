from unittest import TestCase
from mock import patch, sentinel, ANY
import json
import responses

from lintreview.config import build_review_config
from lintreview.diff import DiffCollection
from lintreview.processor import Processor
from lintreview.fixers.error import ConfigurationError, WorkflowError

from . import load_fixture, test_dir, requires_image, fixer_ini, create_repo


app_config = {
    'GITHUB_OAUTH_TOKEN': 'fake-token',
    'GITHUB_AUTHOR_NAME': 'bot',
    'GITHUB_AUTHOR_EMAIL': 'bot@example.com',
    'SUMMARY_THRESHOLD': 50,
}


class TestProcessor(TestCase):

    def setUp(self):
        self.tool_patcher = patch('lintreview.processor.tools')
        self.tool_stub = self.tool_patcher.start()
        self.fixer_patcher = patch('lintreview.processor.fixers')
        self.fixer_stub = self.fixer_patcher.start()

    def tearDown(self):
        self.tool_patcher.stop()
        self.fixer_patcher.stop()

    @responses.activate
    def test_load_changes(self):
        repo = create_repo()
        pull = repo.pull_request(1)

        config = build_review_config('', app_config)
        subject = Processor(repo, pull, './tests', config)
        subject.load_changes()

        assert subject._changes
        assert isinstance(subject._changes, DiffCollection)
        assert 1 == len(subject._changes), 'File count is wrong'

    @responses.activate
    def test_run_tools__no_changes(self):
        repo = create_repo()
        pull = repo.pull_request(1)

        config = build_review_config('', app_config)
        subject = Processor(repo, pull, './tests', config)
        self.assertRaises(RuntimeError,
                          subject.run_tools)

    @responses.activate
    def test_run_tools__import_error(self):
        self.tool_patcher.stop()
        repo = create_repo()
        pull = repo.pull_request(1)

        ini = """
[tools]
linters = nope
"""
        config = build_review_config(ini, app_config)
        subject = Processor(repo, pull, './tests', config)
        subject.load_changes()
        subject.run_tools()
        self.tool_patcher.start()

        problems = subject.problems.all()

        assert len(problems) == 1
        assert 'could not load linters' in problems[0].body

    @responses.activate
    def test_run_tools__ignore_patterns(self):
        repo = create_repo()
        pull = repo.pull_request(1)

        config = build_review_config(fixer_ini, app_config)
        config.ignore_patterns = lambda: ['View/Helper/*']

        subject = Processor(repo, pull, './tests', config)
        subject.load_changes()
        subject.run_tools()

        self.tool_stub.run.assert_called_with(
            ANY,
            [],
            ANY
        )

    @responses.activate
    def test_run_tools__execute_fixers(self):
        repo = create_repo()
        pull = repo.pull_request(1)

        self.tool_stub.factory.return_value = sentinel.tools

        self.fixer_stub.create_context.return_value = sentinel.context
        self.fixer_stub.run_fixers.return_value = sentinel.diff

        config = build_review_config(fixer_ini, app_config)
        subject = Processor(repo, pull, './tests', config)
        subject.load_changes()
        subject.run_tools()

        file_path = 'View/Helper/AssetCompressHelper.php'
        self.fixer_stub.create_context.assert_called_with(
            config,
            './tests',
            repo,
            pull
        )
        self.fixer_stub.run_fixers.assert_called_with(
            sentinel.tools,
            './tests',
            [file_path]
        )
        self.fixer_stub.apply_fixer_diff.assert_called_with(
            subject._changes,
            sentinel.diff,
            sentinel.context
        )
        self.tool_stub.run.assert_called()

    @responses.activate
    def test_run_tools__execute_fixers_fail(self):
        repo = create_repo()
        pull = repo.pull_request(1)

        self.tool_stub.factory.return_value = sentinel.tools

        self.fixer_stub.create_context.return_value = sentinel.context
        self.fixer_stub.run_fixers.side_effect = RuntimeError

        config = build_review_config(fixer_ini, app_config)
        subject = Processor(repo, pull, './tests', config)
        subject.load_changes()
        subject.run_tools()

        self.fixer_stub.create_context.assert_called()
        self.fixer_stub.run_fixers.assert_called()
        self.fixer_stub.apply_fixer_diff.assert_not_called()
        self.fixer_stub.rollback_changes.assert_called()
        self.tool_stub.run_assert_called()

    @responses.activate
    def test_run_tools_fixer_error_scenario(self):
        errors = [
            WorkflowError('A bad workflow thing'),
            ConfigurationError('A bad configuration thing'),
        ]
        for error in errors:
            self.tool_stub.reset()
            self.fixer_stub.reset()
            self._test_run_tools_fixer_error_scenario(error)

    def _test_run_tools_fixer_error_scenario(self, error):
        repo = create_repo()
        pull = repo.pull_request(1)

        self.tool_stub.factory.return_value = sentinel.tools

        self.fixer_stub.create_context.return_value = sentinel.context
        self.fixer_stub.apply_fixer_diff.side_effect = error

        config = build_review_config(fixer_ini, app_config)
        subject = Processor(repo, pull, './tests', config)
        subject.load_changes()
        subject.run_tools()

        self.fixer_stub.create_context.assert_called()
        self.fixer_stub.run_fixers.assert_called()
        self.tool_stub.run.assert_called()
        self.fixer_stub.rollback_changes.assert_called_with('./tests', pull.head)

        assert subject.problems
        assert 1 == len(subject.problems), 'strategy error adds pull comment'
        assert 0 == subject.problems.error_count(), 'fixer failure should be info level'

        assert 'Unable to apply fixers. ' + str(error) == subject.problems.all()[0].body
        assert 1 == len(subject.problems), 'strategy error adds pull comment'


class TestProcessorIntegration(TestCase):
    @responses.activate
    @requires_image('php')
    def test_execute__integration(self):
        repo = create_repo()
        pull = repo.pull_request(1)

        file_url = 'https://api.github.com/repos/markstory/lint-test/pulls/1/files'
        responses.replace(
            responses.GET,
            file_url,
            json=json.loads(load_fixture('integration_test_files.json'))
        )
        responses.add_passthru('http+docker://localhost')

        config = """
[tools]
linters = phpcs
"""
        config = build_review_config(config, app_config)
        subject = Processor(repo, pull, test_dir, config)
        subject.load_changes()
        review, problems = subject.execute()

        assert review is not None
        assert problems is not None
        assert len(problems) > 0
