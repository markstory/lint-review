import lintreview.tools as tools
import github3
from lintreview.config import ReviewConfig, build_review_config
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
    config = build_review_config(bad_ini)
    config = ReviewConfig()
    config.load_ini(bad_ini)
    tools.factory(Review(gh, None), config, '')


def test_factory_generates_tools():
    gh = Mock(spec=github3.GitHub)
    config = build_review_config(sample_ini)
    linters = tools.factory(Review(gh, None), config, '')
    eq_(2, len(linters))
    assert isinstance(linters[0], tools.pep8.Pep8)
    assert isinstance(linters[1], tools.jshint.Jshint)


def test_tool_constructor__config():
    problems = Problems()
    config = {'good': 'value'}
    tool = tools.Tool(problems, config)
    eq_(tool.options, config)

    tool = tools.Tool(problems, 'derp')
    eq_(tool.options, {})

    tool = tools.Tool(problems, 2)
    eq_(tool.options, {})

    tool = tools.Tool(problems, None)
    eq_(tool.options, {})


def test_run():
    config = build_review_config(simple_ini)
    problems = Problems()
    files = ['./tests/fixtures/pep8/has_errors.py']
    tools.run(config, problems, files, [], '')
    eq_(6, len(problems))


def test_run__filter_files():
    config = build_review_config(simple_ini)
    problems = Problems()
    files = [
        './tests/fixtures/pep8/has_errors.py',
        './tests/fixtures/phpcs/has_errors.php'
    ]
    tools.run(config, problems, files, [], '')
    eq_(6, len(problems))
