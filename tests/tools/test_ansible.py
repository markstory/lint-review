from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.tools.ansible import Ansible
from unittest import TestCase
from nose.tools import eq_


class TestAnsible(TestCase):

    fixtures = [
        'tests/fixtures/ansible/no_errors.yml',
        'tests/fixtures/ansible/has_errors.yml',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Ansible(self.problems)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.yml'))
        self.assertTrue(self.tool.match_file('dir/name/test.yml'))

    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(11, len(problems))

        fname = self.fixtures[1]
        expected = Comment(
            fname, 12, 12,
            '[EANSIBLE0012] Commands should not change things if nothing needs doing'  # noqa
        )
        eq_(expected, problems[0])

        expected = Comment(
            fname, 18, 18,
            '[EANSIBLE0004] Git checkouts must contain explicit version'  # noqa
        )
        eq_(expected, problems[3])

    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        eq_(11, len(problems))
        expected = Comment(
            self.fixtures[1], 12, 12,
            '[EANSIBLE0012] Commands should not change things if nothing needs doing'  # noqa
        )
        eq_(expected, problems[0])

        expected = Comment(
            self.fixtures[1], 27, 27,
            '[EANSIBLE0006] git used in place of git module'
        )
        eq_(expected, problems[5])

    def test_config_options_and_process_file(self):
        options = {
            'ignore': 'ANSIBLE0012,ANSIBLE0006'
        }
        self.tool = Ansible(self.problems, options)
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        eq_(7, len(problems))
        for p in problems:
            self.assertFalse('ANSIBLE0012' in p.body)
            self.assertFalse('ANSIBLE0006' in p.body)
