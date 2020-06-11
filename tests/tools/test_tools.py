from unittest import TestCase
from mock import Mock, patch

import lintreview.tools as tools
from lintreview.config import ReviewConfig, build_review_config
from lintreview.docker import TimeoutError
from lintreview.review import Review, Problems, Comment
from lintreview.tools import pep8, jshint
from tests import root_dir, fixtures_path, requires_image

import github3


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


class TestFactory(TestCase):

    def test_factory_raises_error_on_bad_linter(self):
        gh = Mock(spec=github3.GitHub)
        config = ReviewConfig()
        config.load_ini(bad_ini)
        self.assertRaises(ImportError, tools.factory, config,
                          Review(gh, None, config), '')

    def test_tool_repr(self):
        gh = Mock(spec=github3.GitHub)
        config = build_review_config(sample_ini)
        linters = tools.factory(config, Review(gh, None, config), '')
        self.assertIn('<pep8Tool config:', str(linters[0]))

    def test_factory_generates_tools(self):
        gh = Mock(spec=github3.GitHub)
        config = build_review_config(sample_ini)
        linters = tools.factory(config, Review(gh, None, config), '')
        self.assertEqual(2, len(linters))
        self.assertIsInstance(linters[0], pep8.Pep8)
        self.assertIsInstance(linters[1], jshint.Jshint)


class TestToolBase(TestCase):

    def test_tool_constructor__config(self):
        problems = Problems()
        config = {'good': 'value'}
        tool = tools.Tool(problems, config)
        self.assertEqual(tool.options, config)

        tool = tools.Tool(problems, 'derp')
        self.assertEqual(tool.options, {})

        tool = tools.Tool(problems, 2)
        self.assertEqual(tool.options, {})

        tool = tools.Tool(problems, None)
        self.assertEqual(tool.options, {})

    def test_tool_apply_base__no_base(self):
        problems = Problems()
        tool = tools.Tool(problems, {})

        result = tool.apply_base('comments_current.json')
        self.assertEqual(result, 'comments_current.json')

    def test_tool_apply_base__with_base(self):
        problems = Problems()
        tool = tools.Tool(problems, {}, fixtures_path)

        result = tool.apply_base('comments_current.json')
        self.assertEqual(result, fixtures_path + '/comments_current.json')

        result = tool.apply_base('./comments_current.json')
        self.assertEqual(result, fixtures_path + '/comments_current.json')

        result = tool.apply_base('eslint/config.json')
        self.assertEqual(result, fixtures_path + '/eslint/config.json')

        result = tool.apply_base('./eslint/config.json')
        self.assertEqual(result, fixtures_path + '/eslint/config.json')

        result = tool.apply_base('../fixtures/eslint/config.json')
        self.assertEqual(result, fixtures_path + '/eslint/config.json')

    def test_tool_apply_base__with_base_no_traversal(self):
        problems = Problems()
        tool = tools.Tool(problems, {}, fixtures_path)

        result = tool.apply_base('../../../comments_current.json')
        self.assertEqual(result, 'comments_current.json')

    @requires_image('python2')
    def test_run(self):
        config = build_review_config(simple_ini)
        problems = Problems()
        files = ['./tests/fixtures/pep8/has_errors.py']
        tool_list = tools.factory(config, problems, root_dir)
        tools.run(tool_list, files, [])
        self.assertEqual(7, len(problems))

    @requires_image('python2')
    def test_run__filter_files(self):
        config = build_review_config(simple_ini)
        problems = Problems()
        files = [
            './tests/fixtures/pep8/has_errors.py',
            './tests/fixtures/phpcs/has_errors.php'
        ]
        tool_list = tools.factory(config, problems, root_dir)
        tools.run(tool_list, files, [])
        self.assertEqual(7, len(problems))

    @patch('lintreview.docker.run')
    def test_run_timeout_error(self, mock_docker):
        mock_docker.side_effect = TimeoutError(
            "Read timed out. (read timeout=300)")
        config = build_review_config(simple_ini)
        problems = Problems()
        files = ['./tests/fixtures/pep8/has_errors.py']
        tool_list = tools.factory(config, problems, root_dir)
        tools.run(tool_list, files, [])

        errors = problems.all()
        assert 1 == len(errors)
        assert 'timed out during' in errors[0].body
        assert 'run pep8 linter' in errors[0].body


class TestPythonImage(TestCase):
    def test(self):
        self.assertEqual('python2', tools.python_image(False))
        self.assertEqual('python2', tools.python_image(''))
        self.assertEqual('python2', tools.python_image('derp'))
        self.assertEqual('python2', tools.python_image({}))
        self.assertEqual('python2', tools.python_image([]))
        self.assertEqual('python2', tools.python_image({'python': 2}))
        self.assertEqual('python2', tools.python_image({'python': '2'}))
        self.assertEqual('python3', tools.python_image({'python': '3'}))
        self.assertEqual('python3', tools.python_image({'python': 3}))


class TestProcessCheckstyle(TestCase):
    def test_process(self):
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
        self.assertEqual(3, len(problems))

        things = problems.all('things.py')
        self.assertEqual(2, len(things))
        self.assertEqual(1, things[0].line)
        self.assertEqual('Not good', things[0].body)

    def test_comma_lines(self):
        problems = Problems()
        xml = """
    <checkstyle>
      <file name="other_things.py">
        <error line="3,4,5" message="Not good" />
      </file>
    </checkstyle>
    """
        tools.process_checkstyle(problems, xml, lambda x: x)
        self.assertEqual(3, len(problems))

        things = problems.all('other_things.py')
        self.assertEqual(3, len(things))
        self.assertEqual(3, things[0].line)
        self.assertEqual('Not good', things[0].body)

        self.assertEqual(4, things[1].line)
        self.assertEqual('Not good', things[1].body)

        self.assertEqual(5, things[2].line)
        self.assertEqual('Not good', things[2].body)

    def test_process_undefined(self):
        problems = Problems()
        xml = """
    <checkstyle>
      <file name="other_things.py">
        <error line="undefined" message="Not good" />
      </file>
    </checkstyle>
    """
        tools.process_checkstyle(problems, xml, lambda x: x)
        self.assertEqual(1, len(problems))
        errors = problems.all('other_things.py')
        assert len(errors) == 1, errors
        assert errors[0].line == Comment.FIRST_LINE_IN_DIFF
        assert errors[0].body == 'Not good'


class ProcessQuickfix(TestCase):
    def test(self):
        problems = Problems()
        text = """
/src/file.py:1:1: A message.
/src/dir/file.text:10:1: Another message
"""
        tools.process_quickfix(problems, text.splitlines(), lambda x: x)
        assert len(problems) == 2
        filepy = problems.all('/src/file.py')[0]
        assert 1 == filepy.position
        assert 1 == filepy.line
        assert 'A message.' == filepy.body

        filetext = problems.all('/src/dir/file.text')[0]
        assert 10 == filetext.position
        assert 10 == filetext.line
        assert 'Another message' == filetext.body

    def test_invalid_content(self):
        problems = Problems()
        text = """
Error: No such file or directory: /src/main.rb
/src/readme.txt:8:1: Bad words.
"""
        tools.process_quickfix(problems, text.splitlines(), lambda x: x)
        assert len(problems) == 1
        assert 8 == problems.all('/src/readme.txt')[0].line

    def test_extra_colons(self):
        problems = Problems()
        text = """
/src/styles.css:8:1: invalid selector .thing::before
"""
        tools.process_quickfix(problems, text.splitlines(), lambda x: x)
        assert len(problems) == 1
        error = problems.all('/src/styles.css')[0]
        assert 8 == error.line
        assert 'invalid selector .thing::before' == error.body
