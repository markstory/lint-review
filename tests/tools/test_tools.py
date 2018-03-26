from __future__ import absolute_import
import lintreview.tools as tools
import github3
from lintreview.config import ReviewConfig, build_review_config
from lintreview.review import Review, Problems
from nose.tools import eq_, raises
from mock import Mock
from tests import root_dir, fixtures_path, requires_image


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
    tools.factory(config, Review(gh, None), '')


def test_factory_generates_tools():
    gh = Mock(spec=github3.GitHub)
    config = build_review_config(sample_ini)
    linters = tools.factory(config, Review(gh, None), '')
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


def test_tool_apply_base__no_base():
    problems = Problems()
    tool = tools.Tool(problems, {})

    result = tool.apply_base('comments_current.json')
    eq_(result, 'comments_current.json')


def test_tool_apply_base__with_base():
    problems = Problems()
    tool = tools.Tool(problems, {}, fixtures_path)

    result = tool.apply_base('comments_current.json')
    eq_(result, fixtures_path + '/comments_current.json')

    result = tool.apply_base('./comments_current.json')
    eq_(result, fixtures_path + '/comments_current.json')

    result = tool.apply_base('eslint/config.json')
    eq_(result, fixtures_path + '/eslint/config.json')

    result = tool.apply_base('./eslint/config.json')
    eq_(result, fixtures_path + '/eslint/config.json')

    result = tool.apply_base('../fixtures/eslint/config.json')
    eq_(result, fixtures_path + '/eslint/config.json')


def test_tool_apply_base__with_base_no_traversal():
    problems = Problems()
    tool = tools.Tool(problems, {}, fixtures_path)

    result = tool.apply_base('../../../comments_current.json')
    eq_(result, 'comments_current.json')


@requires_image('python2')
def test_run():
    config = build_review_config(simple_ini)
    problems = Problems()
    files = ['./tests/fixtures/pep8/has_errors.py']
    tool_list = tools.factory(config, problems, root_dir)
    tools.run(tool_list, files, [])
    eq_(7, len(problems))


@requires_image('python2')
def test_run__filter_files():
    config = build_review_config(simple_ini)
    problems = Problems()
    files = [
        './tests/fixtures/pep8/has_errors.py',
        './tests/fixtures/phpcs/has_errors.php'
    ]
    tool_list = tools.factory(config, problems, root_dir)
    tools.run(tool_list, files, [])
    eq_(7, len(problems))


def test_python_image():
    eq_('python2', tools.python_image(False))
    eq_('python2', tools.python_image(''))
    eq_('python2', tools.python_image('derp'))
    eq_('python2', tools.python_image({}))
    eq_('python2', tools.python_image([]))
    eq_('python2', tools.python_image({'python': 2}))
    eq_('python2', tools.python_image({'python': '2'}))
    eq_('python3', tools.python_image({'python': '3'}))
    eq_('python3', tools.python_image({'python': 3}))


def test_process_checkstyle():
    problems = Problems()
    xml = """
<checkstyle>
  <file name="things.py">
    <error line="1" message="Not good" />
    <error line="2" message="Also not good" />
  </file>
  <file name="other_things.py">
    <error line="3" message="Not good" />
  </file>
</checkstyle>
"""
    tools.process_checkstyle(problems, xml, lambda x: x)
    eq_(3, len(problems))

    things = problems.all('things.py')
    eq_(2, len(things))
    eq_(1, things[0].line)
    eq_('Not good', things[0].body)


def test_process_checkstyle__comma_lines():
    problems = Problems()
    xml = """
<checkstyle>
  <file name="other_things.py">
    <error line="3,4,5" message="Not good" />
  </file>
</checkstyle>
"""
    tools.process_checkstyle(problems, xml, lambda x: x)
    eq_(3, len(problems))

    things = problems.all('other_things.py')
    eq_(3, len(things))
    eq_(3, things[0].line)
    eq_('Not good', things[0].body)

    eq_(4, things[1].line)
    eq_('Not good', things[1].body)

    eq_(5, things[2].line)
    eq_('Not good', things[2].body)


def test_process_checkstyle__non_int():
    problems = Problems()
    xml = """
<checkstyle>
  <file name="other_things.py">
    <error line="undefined" message="Not good" />
  </file>
</checkstyle>
"""
    tools.process_checkstyle(problems, xml, lambda x: x)
    eq_(0, len(problems))
