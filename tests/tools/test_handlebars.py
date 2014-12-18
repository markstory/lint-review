from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.tools.unsafe_handlebars import UnsafeHandlebars
from lintreview.utils import in_path
from lintreview.utils import npm_exists
from unittest import TestCase
from unittest import skipIf
from nose.tools import eq_

grep_missing = not(in_path('grep') or npm_exists('grep'))


class TestUnsafeHandlebars(TestCase):

    needs_grep = skipIf(grep_missing, 'Needs grep to run')

    fixtures = [
        'tests/fixtures/unsafe_handlebars/no_errors.hbs',
        'tests/fixtures/unsafe_handlebars/has_errors.hbs',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = UnsafeHandlebars(self.problems)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.js'))
        self.assertTrue(self.tool.match_file('dir/name/test.js'))
        self.assertTrue(self.tool.match_file('test.hbs'))
        self.assertTrue(self.tool.match_file('dir/name/test.hbs'))

    @needs_grep
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @needs_grep
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @needs_grep
    def test_process_files__multiple_error(self):
        msg = """
:warning: Warning! Potential XSS vulnerability. Are you sure you intended to use 3 curlybraces?

```
%s
```
"""
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(6, len(problems))

        fname = self.fixtures[1]
        expected = Comment(fname, 4, 4, msg % "{{{query}}}")
        eq_(expected, problems[0])

        expected = Comment(fname, 7, 7, msg % "<p>It's {{{meta.words}}} long. That's about a {{{meta.minutesToRead}}} minute read.</p>")
        eq_(expected, problems[1])

        expected = Comment(fname, 10, 10, msg % "{{{~ranOutOfIdeas~}}}")
        eq_(expected, problems[2])

    @needs_grep
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(6, len(problems))

    def test_create_command__with_path_based_standard(self):
        tool = UnsafeHandlebars(self.problems, None, '/some/path')
        result = tool.create_command(['some/file.hbs'])
        expected = [
            '-nR',
            '"{{{~\?[A-Za-z.]\+~\?}}}"',
            'some/file.hbs'
        ]
        assert 'grep' in result[0], 'grep is in command name'
        eq_(result[1:], expected)
