from __future__ import absolute_import
import os
import lintreview.fixers as fixers
from lintreview.config import build_review_config
from lintreview.diff import parse_diff, Diff
from lintreview.tools.phpcs import Phpcs
from lintreview.utils import composer_exists
from unittest import skipIf
from mock import Mock
from nose.tools import (
    assert_raises,
    assert_in,
    eq_,
    with_setup
)
from .. import load_fixture, fixtures_path, fixer_ini
from ..test_git import setup_repo, teardown_repo, clone_path


app_config = {
    'GITHUB_AUTHOR': 'bot <bot@example.com>'
}

phpcs_missing = not(composer_exists('phpcs'))


def test_run_fixers():
    # Test that fixers are executed if fixer is enabled
    mock_tool = Mock()
    mock_tool.has_fixer.return_value = True
    files = ['diff/adjacent_original.txt']

    out = fixers.run_fixers([mock_tool], fixtures_path, files)
    eq_(1, mock_tool.execute_fixer.call_count)
    eq_(0, len(out))


def test_run_fixers__no_fixer_mode():
    # Test that fixers are skipped when has_fixer fails
    # Test that fixers are executed if fixer is enabled
    mock_tool = Mock()
    mock_tool.has_fixer.return_value = False
    files = ['diff/adjacent_original.txt']

    out = fixers.run_fixers([mock_tool], fixtures_path, files)
    eq_(0, mock_tool.execute_fixer.call_count)
    eq_(0, len(out))


@skipIf(phpcs_missing, 'Needs phpcs')
@with_setup(setup_repo, teardown_repo)
def test_run_fixers__integration():
    # Test fixer integration with phpcs.
    tail_path = 'tests/fixtures/phpcs/has_errors.php'
    file_path = os.path.abspath(clone_path + '/' + tail_path)
    phpcs = Phpcs(Mock(), {'fixer': True})

    diff = fixers.run_fixers([phpcs], clone_path, [file_path])
    eq_(1, len(diff))
    eq_(tail_path, diff[0].filename)


def test_find_intersecting_diffs():
    original = load_fixture('diff/intersecting_hunks_original.txt')
    updated = load_fixture('diff/intersecting_hunks_updated.txt')
    original = parse_diff(original)
    updated = parse_diff(updated)
    result = fixers.find_intersecting_diffs(original, updated)

    eq_(1, len(result))
    assert isinstance(result[0], Diff)
    eq_('model.php', result[0].filename)
    eq_('00000', result[0].commit)


def test_find_intersecting_diffs__no_intersect():
    original = load_fixture('diff/intersecting_hunks_original.txt')
    updated = load_fixture('diff/adjacent_original.txt')
    original = parse_diff(original)
    updated = parse_diff(updated)
    result = fixers.find_intersecting_diffs(original, updated)

    eq_(0, len(result))


def test_apply_fixer_diff__missing_strategy_key():
    original = Mock()
    changed = Mock()
    context = {}
    with assert_raises(fixers.StrategyError) as err:
        fixers.apply_fixer_diff(original, changed, context)
    assert_in('Missing', str(err.exception))


def test_apply_fixer_diff__invalid_strategy():
    original = Mock()
    changed = Mock()
    context = {'strategy': 'bad stategy'}
    with assert_raises(fixers.StrategyError) as err:
        fixers.apply_fixer_diff(original, changed, context)
    assert_in('Unknown', str(err.exception))


def test_apply_fixer_diff__missing_strategy_context():
    original = Mock()
    changed = Mock()
    context = {'strategy': 'commit'}
    with assert_raises(fixers.StrategyError) as err:
        fixers.apply_fixer_diff(original, changed, context)
    assert_in('Could not create strategy', str(err.exception))


def test_apply_fixer_diff__strategy_execution_fails():
    strategy_factory = Mock()
    strategy = Mock()
    strategy.execute.side_effect = RuntimeError
    strategy_factory.return_value = strategy

    fixers.add_strategy('mock', strategy_factory)

    original = load_fixture('diff/intersecting_hunks_original.txt')
    updated = load_fixture('diff/intersecting_hunks_updated.txt')
    original = parse_diff(original)
    updated = parse_diff(updated)

    context = {'strategy': 'mock'}
    out = fixers.apply_fixer_diff(original, updated, context)
    eq_(1, strategy.execute.call_count)
    eq_(out, None, 'No output and no exception')


def test_apply_fixer_diff__calls_execute():
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
    eq_(1, strategy.execute.call_count)


def test_create_context():
    config = build_review_config(fixer_ini)
    context = fixers.create_context(config, app_config, clone_path, 'fixes')
    eq_('commit', context['strategy'])
    eq_(app_config['GITHUB_AUTHOR'], context['author'])
    eq_(clone_path, context['repo_path'])
    eq_('fixes', context['remote_branch'])


def test_create_context__missing_key_raises():
    config = build_review_config(fixer_ini)
    with assert_raises(KeyError):
        empty = {}
        fixers.create_context(config, empty, clone_path, 'fixes')
