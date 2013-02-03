import lintreview.tools as tools
from lintreview.config import ReviewConfig
from lintreview.review import Review
from nose.tools import eq_
from nose.tools import raises

sample_ini = """
[tools]
linters = pep8, jshint

[tool_jshint]
config = ./jshint.json

"""

bad_ini = """
[tools]
linters = not there, bogus
"""


@raises(ImportError)
def test_factory_raises_error_on_bad_linter():
    config = ReviewConfig(bad_ini)
    tools.factory(Review(None), config)


def test_factory_generates_tools():
    config = ReviewConfig(sample_ini)
    linters = tools.factory(Review(None), config)
    eq_(2, len(linters))
    assert isinstance(linters[0], tools.pep8.Pep8)
    assert isinstance(linters[1], tools.jshint.Jshint)
