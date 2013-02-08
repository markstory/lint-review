from lintreview.config import load_config
from lintreview.config import ReviewConfig
from nose.tools import eq_
from unittest import TestCase

sample_ini = """
[tools]
linters = phpcs, pep8, jshint

[tool_jshint]
config = ./jshint.json

[tool_phpcs]
standard = test/CodeStandards
config = test/phpcs.xml
"""

bad_ini = """
[herp]
derp=derplily
"""


def test_load_config():
    res = load_config()
    assert res['GITHUB_USER'].endswith, 'Exists and is stringy'


class ReviewConfigTest(TestCase):

    def test_linter_listing_bad(self):
        config = ReviewConfig(bad_ini)
        res = config.linters()
        eq_(res, None)

    def test_linter_listing(self):
        config = ReviewConfig(sample_ini)
        res = config.linters()
        expected = ['phpcs', 'pep8', 'jshint']
        eq_(res, expected)

    def test_linter_config_bad(self):
        config = ReviewConfig(bad_ini)
        res = config.linter_config('phpcs')
        eq_(res, None)

    def test_linter_config(self):
        config = ReviewConfig(sample_ini)
        res = config.linter_config('phpcs')
        expected = {
            'standard': 'test/CodeStandards',
            'config': 'test/phpcs.xml'
        }
        eq_(res, expected)

        res = config.linter_config('not there')
        eq_(res, None)
