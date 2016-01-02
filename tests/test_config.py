from unittest import TestCase

from nose.tools import eq_

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

bad_ini = """
[herp]
derp=derplily
"""


def test_load_config():
    res = load_config()
    assert res['GITHUB_USER'].endswith, 'Exists and is stringy'


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
