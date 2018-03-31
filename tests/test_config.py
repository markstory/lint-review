from __future__ import absolute_import
from unittest import TestCase

from nose.tools import eq_, raises

from lintreview.config import build_review_config, get_lintrc_defaults
from lintreview.config import load_config, ReviewConfig

sample_ini = """
[files]
ignore = test/CodeStandards/test/**
    vendor/**

[tools]
linters = phpcs, pep8, jshint

[tool_jshint]
config = ./jshint.json

[tool_phpcs]
standard = test/CodeStandards
config = test/phpcs.xml
"""

defaults_ini = """
[tool_jshint]
config = /etc/jshint.json
"""

simple_ini = """
[tools]
linters = jshint
"""

fixer_ini = """
[tools]
linters = phps

[fixers]
enable = True
workflow = pull_request
"""

review_ini = """
[tools]
linters = jshint

[review]
summary_comment_threshold = 25
fail_on_comments = False
apply_label_on_pass = lint ok
"""

fixer_ini = """
[tools]
linters = phps

[fixers]
enable = True
workflow = pull_request
"""

bad_ini = """
[herp]
derp=derplily
"""

# Simulate the application config
app_config = {
    'SUMMARY_THRESHOLD': 100,
    'OK_LABEL': 'no lint',
    'PULLREQUEST_STATUS': True
}


def test_load_config():
    res = load_config()
    assert res['GITHUB_URL'].endswith, 'Exists and is stringy'


def test_get_lintrc_defaults():
    config = load_config()
    res = get_lintrc_defaults(config)
    assert res is None


def test_build_review_config():
    config = build_review_config(sample_ini, {})
    assert isinstance(config, ReviewConfig)
    eq_(3, len(config.linters()))


class ReviewConfigTest(TestCase):

    def test_linter_listing_bad(self):
        config = build_review_config(bad_ini)
        res = config.linters()
        eq_(res, [])

    def test_linter_listing(self):
        config = build_review_config(sample_ini)
        res = config.linters()
        expected = ['phpcs', 'pep8', 'jshint']
        eq_(sorted(res), sorted(expected))

    def test_linter_config_bad(self):
        config = build_review_config(bad_ini)
        res = config.linter_config('phpcs')
        eq_(res, {})

    def test_linter_config(self):
        config = build_review_config(sample_ini)
        res = config.linter_config('phpcs')
        expected = {
            'standard': 'test/CodeStandards',
            'config': 'test/phpcs.xml'
        }
        eq_(res, expected)

        res = config.linter_config('not there')
        eq_(res, {})

    def test_ignore_patterns(self):
        config = build_review_config(sample_ini)
        res = config.ignore_patterns()
        expected = ['test/CodeStandards/test/**', 'vendor/**']
        eq_(res, expected)

    def test_ignore_patterns_missing(self):
        config = ReviewConfig()
        res = config.ignore_patterns()
        eq_(res, [])

    def test_load_ini__override(self):
        config = ReviewConfig()
        config.load_ini(defaults_ini)
        config.load_ini(sample_ini)
        res = config.linter_config('jshint')
        expected = {
            'config': './jshint.json',
        }
        eq_(res, expected)

    def test_load_ini__multiple_merges_settings(self):
        config = ReviewConfig()
        config.load_ini(defaults_ini)
        config.load_ini(simple_ini)
        res = config.linter_config('jshint')
        expected = {
            'config': '/etc/jshint.json',
        }
        eq_(res, expected)

    def test_fixers_enabled(self):
        config = build_review_config(sample_ini)
        eq_(False, config.fixers_enabled())

        config = build_review_config(fixer_ini)
        eq_(True, config.fixers_enabled())

    def test_fixer_workflow(self):
        config = build_review_config(sample_ini)
        eq_('commit', config.fixer_workflow())

        config = build_review_config(fixer_ini)
        eq_('pull_request', config.fixer_workflow())

    def test_getitem(self):
        config = build_review_config(simple_ini, app_config)
        eq_(app_config['SUMMARY_THRESHOLD'], config['SUMMARY_THRESHOLD'])

    @raises(IndexError)
    def test_getitem__error(self):
        config = build_review_config(simple_ini, app_config)
        config['UNKNOWN']

    def test_get(self):
        config = build_review_config(simple_ini, app_config)
        eq_(app_config['SUMMARY_THRESHOLD'], config.get('SUMMARY_THRESHOLD'))
        eq_(None, config.get('unknown'))
        eq_('default', config.get('unknown', 'default'))

    def test_summary_threshold__undefined(self):
        config = build_review_config(simple_ini)
        eq_(None, config.summary_threshold())

    def test_summary_threshold__app_config(self):
        config = build_review_config(simple_ini, app_config)
        eq_(app_config['SUMMARY_THRESHOLD'], config.summary_threshold())

    def test_summary_threshold__job_config(self):
        config = build_review_config(review_ini, app_config)
        eq_(25, config.summary_threshold())

    def test_review_passed_label__undefined(self):
        config = build_review_config(simple_ini)
        eq_(None, config.review_passed_label())

    def test_review_passed_label__app_config(self):
        config = build_review_config(simple_ini, app_config)
        eq_('no lint', config.review_passed_label())

    def test_review_passed_label__job_config(self):
        config = build_review_config(review_ini, app_config)
        eq_('lint ok', config.review_passed_label())

    def test_failed_review_status__undefined(self):
        config = build_review_config(simple_ini)
        eq_('failure', config.failed_review_status())

    def test_failed_review_status__app_config(self):
        config = build_review_config(simple_ini, {'PULLREQUEST_STATUS': True})
        eq_('failure', config.failed_review_status())

        config = build_review_config(simple_ini, {'PULLREQUEST_STATUS': False})
        eq_('success', config.failed_review_status())

    def test_failed_review_status__job_config(self):
        config = build_review_config(review_ini, app_config)
        eq_('success', config.failed_review_status())

        ini = "[review]\nfail_on_comments = true"
        config = build_review_config(ini, app_config)
        eq_('failure', config.failed_review_status())
