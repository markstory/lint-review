import lintreview.tools as tools
import github3
from lintreview.config import ReviewConfig
from lintreview.review import Review
from lintreview.review import Problems
from nose.tools import eq_, raises
from mock import Mock


sample_ini = """
[tools]
linters = pep8, jshint

[tool_jshint]
config = ./jshint.json

"""


simple_ini = """
[tools]
linters = pep8
"""

bad_ini = """
[tools]
linters = not there, bogus
"""


@raises(ImportError)
def test_factory_raises_error_on_bad_linter():
    gh = Mock(spec=github3.GitHub)
    config = ReviewConfig(bad_ini)
    tools.factory(Review(gh, None), config, '')


def test_factory_generates_tools():
    gh = Mock(spec=github3.GitHub)
    config = ReviewConfig(sample_ini)
    linters = tools.factory(Review(gh, None), config, '')
    eq_(2, len(linters))
    assert isinstance(linters[0], tools.pep8.Pep8)
    assert isinstance(linters[1], tools.jshint.Jshint)


def test_run():
    config = ReviewConfig(simple_ini)
    problems = Problems()
    files = ['./tests/fixtures/pep8/has_errors.py']
    tools.run(config, problems, files, [], '')
    eq_(6, len(problems))


def test_run__filter_files():
    config = ReviewConfig(simple_ini)
    problems = Problems()
    files = [
        './tests/fixtures/pep8/has_errors.py',
        './tests/fixtures/phpcs/has_errors.php'
    ]
    tools.run(config, problems, files, [], '')
    eq_(6, len(problems))
