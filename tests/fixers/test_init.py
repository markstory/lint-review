from __future__ import absolute_import
import lintreview.fixers as fixers
import lintreview.git as git
from lintreview.diff import parse_diff, Diff
from mock import Mock
from nose.tools import assert_raises, assert_in, eq_
from .. import load_fixture, fixtures_path


def test_run_fixers():
    # Test that fixers are executed if fixer is enabled
    mock_tool = Mock()
    mock_tool.has_fixer.return_value = False
    files = ['diff/adjacent_original.txt']

    out = fixers.run_fixers([mock_tool], fixtures_path, files)
    eq_(0, mock_tool.execute_fixer.call_count)
    eq_(0, len(out))


def test_run_fixers__no_fixer_mode():
    # Test that fixers are skipped when has_fixer fails
    assert False, 'not done'


def test_run_fixers__integration():
    # Test fixer integration with phpcs.
    assert False, 'not done'


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
    assert False, 'not done'


def test_apply_fixer_diff__strategy_execution_fails():
    assert False, 'not done'


def test_apply_fixer_diff__calls_execute():
    assert False, 'not done'
