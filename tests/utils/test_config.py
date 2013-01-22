from lintreview.utils.config import ReviewConfig
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


class ReviewConfigTest(TestCase):

    def test_linter_bad(self):
        config = ReviewConfig(bad_ini)
        res = config.linters()
        eq_(res, [])

    def test_linter_listing(self):
        config = ReviewConfig(sample_ini)
        res = config.linters()
        expected = ['phpcs', 'pep8', 'jshint']
        eq_(res, expected)

    def test_linter_config(self):
        config = ReviewConfig(sample_ini)
        res = config.linter_config('phpcs')
        expected = {
            'standard': 'test/CodeStandards',
            'config': 'test/phpcs.xml'
        }
        eq_(res, expected)
