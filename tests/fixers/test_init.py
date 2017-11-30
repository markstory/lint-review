from __future__ import absolute_import
import lintreview.fixers as fixers
import lintreview.git as git
from mock import Mock
from nose.tools import raises


def test_run_fixers():
    # Test that fixers are executed if fixer is enabled
    assert False, 'not done'


def test_run_fixers__no_fixer_mode():
    # Test that fixers are skipped when has_fixer fails
    assert False, 'not done'


def test_run_fixers__integration():
    # Test fixer integration with phpcs.
    assert False, 'not done'


def test_find_intersecting_diffs():
    # Test intersection of two diff collections.
    assert False, 'not done'


@raises(fixers.StrategyError)
def test_apply_fixer_diff__missing_strategy_key():
    assert False, 'not done'


@raises(fixers.StrategyError)
def test_apply_fixer_diff__invalid_strategy():
    assert False, 'not done'


@raises(fixers.StrategyError)
def test_apply_fixer_diff__missing_strategy_context():
    assert False, 'not done'


def test_apply_fixer_diff__strategy_execution_fails():
    assert False, 'not done'


def test_apply_fixer_diff__calls_execute():
    assert False, 'not done'
