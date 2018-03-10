from __future__ import absolute_import
from lintreview.review import Problems, Comment
from lintreview.tools.pep8 import Pep8
from unittest import TestCase
from nose.tools import eq_, assert_in, assert_not_in
from tests import root_dir, read_file, read_and_restore_file, requires_image


class TestPep8(TestCase):

    fixtures = [
        'tests/fixtures/pep8/no_errors.py',
        'tests/fixtures/pep8/has_errors.py',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Pep8(self.problems, {}, root_dir)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertTrue(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('dir/name/test.py'))

    @requires_image('python2')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @requires_image('python2')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(6, len(problems))

        fname = self.fixtures[1]
        expected = Comment(fname, 2, 2, 'E401 multiple imports on one line')
        eq_(expected, problems[0])

        expected = Comment(fname, 11, 11, "W603 '<>' is deprecated, use '!='")
        eq_(expected, problems[5])

    @requires_image('python2')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(6, len(problems))
        expected = Comment(self.fixtures[1], 2, 2,
                           'E401 multiple imports on one line')
        eq_(expected, problems[0])

        expected = Comment(self.fixtures[1], 11, 11,
                           "W603 '<>' is deprecated, use '!='")
        eq_(expected, problems[5])

    @requires_image('python2')
    def test_process_absolute_container_path(self):
        fixtures = ['/src/' + path for path in self.fixtures]
        self.tool.process_files(fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        assert len(problems) >= 6

    @requires_image('python2')
    def test_process_files__ignore(self):
        options = {
            'ignore': 'E2,W603'
        }
        self.tool = Pep8(self.problems, options, root_dir)
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(4, len(problems))
        for p in problems:
            assert_not_in('E2', p.body)
            assert_not_in('W603', p.body)

    @requires_image('python2')
    def test_process_files__line_length(self):
        options = {
            'max-line-length': '10'
        }
        self.tool = Pep8(self.problems, options, root_dir)
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(10, len(problems))
        expected = Comment(self.fixtures[1], 1, 1,
                           'E501 line too long (23 > 10 characters)')
        eq_(expected, problems[0])

    @requires_image('python2')
    def test_process_files__select(self):
        options = {
            'select': 'W603'
        }
        self.tool = Pep8(self.problems, options, root_dir)
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(1, len(problems))
        for p in problems:
            assert_in('W603', p.body)

    def test_has_fixer__not_enabled(self):
        tool = Pep8(self.problems, {})
        eq_(False, tool.has_fixer())

    def test_has_fixer__enabled(self):
        tool = Pep8(self.problems, {'fixer': True})
        eq_(True, tool.has_fixer())

    @requires_image('python2')
    def test_execute_fixer(self):
        tool = Pep8(self.problems, {'fixer': True}, root_dir)

        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)

        updated = read_and_restore_file(self.fixtures[1], original)
        assert original != updated, 'File content should change.'
        eq_(0, len(self.problems.all()), 'No errors should be recorded')

    @requires_image('python2')
    def test_execute_fixer__options(self):
        tool = Pep8(self.problems, {
            'fixer': True,
            'max-line-length': 120,
            'exclude': 'W201'
        }, root_dir)

        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)

        updated = read_and_restore_file(self.fixtures[1], original)
        assert original != updated, 'File content should change.'
        eq_(0, len(self.problems.all()), 'No errors should be recorded')

    @requires_image('python2')
    def test_execute_fixer__fewer_problems_remain(self):
        tool = Pep8(self.problems, {'fixer': True}, root_dir)

        # The fixture file can have all problems fixed by autopep8
        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)
        tool.process_files(self.fixtures)

        read_and_restore_file(self.fixtures[1], original)
        assert len(self.problems.all()) > 0, 'Most errors should be fixed'
        text = [c.body for c in self.problems.all()]
        assert_in("'<>' is deprecated", ' '.join(text))
