from __future__ import absolute_import
from unittest import TestCase
import lintreview.fixers as fixers
from lintreview.config import build_review_config
from lintreview.diff import parse_diff, Diff
from lintreview.tools.phpcs import Phpcs
from mock import Mock, sentinel
from .. import requires_image, load_fixture, fixtures_path, fixer_ini
from ..test_git import setup_repo, teardown_repo, clone_path


app_config = {
    'GITHUB_AUTHOR_NAME': 'bot',
    'GITHUB_AUTHOR_EMAIL': 'bot@example.com'
}


class TestInit(TestCase):
    def setUp(self):
        setup_repo()

    def tearDown(self):
        teardown_repo()

    def test_run_fixers(self):
        # Test that fixers are executed if fixer is enabled
        mock_tool = Mock()
        mock_tool.has_fixer.return_value = True
        files = ['diff/adjacent_original.txt']

        out = fixers.run_fixers([mock_tool], fixtures_path, files)
        self.assertEqual(1, mock_tool.execute_fixer.call_count)
        self.assertEqual(0, len(out))

    def test_run_fixers__no_fixer_mode(self):
        # Test that fixers are skipped when has_fixer fails
        # Test that fixers are executed if fixer is enabled
        mock_tool = Mock()
        mock_tool.has_fixer.return_value = False
        files = ['diff/adjacent_original.txt']

        out = fixers.run_fixers([mock_tool], fixtures_path, files)
        self.assertEqual(0, mock_tool.execute_fixer.call_count)
        self.assertEqual(0, len(out))

    @requires_image('phpcs')
    def test_run_fixers__integration(self):
        # Test fixer integration with phpcs.
        tail_path = 'tests/fixtures/phpcs/has_errors.php'
        phpcs = Phpcs(Mock(), {'fixer': True}, clone_path)

        diff = fixers.run_fixers([phpcs], clone_path, [tail_path])
        self.assertEqual(1, len(diff))
        self.assertEqual(tail_path, diff[0].filename)

    def test_find_intersecting_diffs(self):
        original = load_fixture('diff/intersecting_hunks_original.txt')
        updated = load_fixture('diff/intersecting_hunks_updated.txt')
        original = parse_diff(original)
        updated = parse_diff(updated)
        result = fixers.find_intersecting_diffs(original, updated)

        self.assertEqual(1, len(result))
        assert isinstance(result[0], Diff)
        self.assertEqual('model.php', result[0].filename)
        self.assertEqual('00000', result[0].commit)

    def test_find_intersecting_diffs__no_intersect(self):
        original = load_fixture('diff/intersecting_hunks_original.txt')
        updated = load_fixture('diff/adjacent_original.txt')
        original = parse_diff(original)
        updated = parse_diff(updated)
        result = fixers.find_intersecting_diffs(original, updated)

        self.assertEqual(0, len(result))

    def test_find_intersecting_diffs__list(self):
        diff = load_fixture('diff/intersecting_hunks_original.txt')
        diffs = parse_diff(diff)

        result = fixers.find_intersecting_diffs(diffs, [])
        self.assertEqual(0, len(result))

        result = fixers.find_intersecting_diffs([], diff)
        self.assertEqual(0, len(result))

    def test_apply_fixer_diff__missing_strategy_key(self):
        original = Mock()
        changed = Mock()
        context = {}

        with self.assertRaises(fixers.ConfigurationError) as err:
            fixers.apply_fixer_diff(original, changed, context)
        self.assertIn('Missing', str(err.exception))

    def test_apply_fixer_diff__invalid_strategy(self):
        original = Mock()
        changed = Mock()
        context = {'strategy': 'bad stategy'}
        with self.assertRaises(fixers.ConfigurationError) as err:
            fixers.apply_fixer_diff(original, changed, context)
        self.assertIn('Unknown', str(err.exception))

    def test_apply_fixer_diff__missing_strategy_context(self):
        original = Mock()
        changed = Mock()
        context = {'strategy': 'commit'}
        with self.assertRaises(fixers.ConfigurationError) as err:
            fixers.apply_fixer_diff(original, changed, context)
        self.assertIn('Could not create commit workflow', str(err.exception))

    def test_apply_fixer_diff__calls_execute(self):
        strategy_factory = Mock()
        strategy = Mock()
        strategy_factory.return_value = strategy

        fixers.add_strategy('mock', strategy_factory)

        original = load_fixture('diff/intersecting_hunks_original.txt')
        updated = load_fixture('diff/intersecting_hunks_updated.txt')
        original = parse_diff(original)
        updated = parse_diff(updated)

        context = {'strategy': 'mock'}
        fixers.apply_fixer_diff(original, updated, context)
        self.assertEqual(1, strategy.execute.call_count)

    def test_apply_fixer_diff__no_intersection(self):
        strategy_factory = Mock()
        strategy = Mock()
        strategy_factory.return_value = strategy

        fixers.add_strategy('mock', strategy_factory)

        original = load_fixture('diff/no_intersect_original.txt')
        updated = load_fixture('diff/no_intersect_updated.txt')
        original = parse_diff(original)
        updated = parse_diff(updated)

        context = {'strategy': 'mock'}
        fixers.apply_fixer_diff(original, updated, context)
        self.assertEqual(0, strategy.execute.call_count)

    def test_create_context(self):
        config = build_review_config(fixer_ini, app_config)
        context = fixers.create_context(
            config, clone_path,
            sentinel.repo, sentinel.pull_request)

        self.assertEqual('commit', context['strategy'])
        self.assertEqual(config['GITHUB_AUTHOR_EMAIL'],
                         context['author_email'])
        self.assertEqual(config['GITHUB_AUTHOR_NAME'], context['author_name'])
        self.assertEqual(clone_path, context['repo_path'])
        self.assertEqual(sentinel.repo, context['repository'])
        self.assertEqual(sentinel.pull_request, context['pull_request'])

    def test_create_context__missing_key_raises(self):
        config = build_review_config(fixer_ini)
        self.assertRaises(KeyError,
                          fixers.create_context,
                          config,
                          clone_path,
                          sentinel.repo,
                          sentinel.pull_request)
