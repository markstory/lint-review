from unittest import TestCase

from lintreview.review import Problems, Comment
from lintreview.tools.ansible import Ansible
from tests import requires_image, root_dir


class TestAnsible(TestCase):

    fixtures = [
        'tests/fixtures/ansible/no_errors.yml',
        'tests/fixtures/ansible/has_errors.yml',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Ansible(self.problems, {}, root_dir)

    def test_version(self):
        assert self.tool.version != ''

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.yml'))
        self.assertTrue(self.tool.match_file('dir/name/test.yml'))

    @requires_image('python2')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        self.assertEqual([], self.problems.all(self.fixtures[0]))

    @requires_image('python2')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(11, len(problems))

        fname = self.fixtures[1]
        expected = Comment(
            fname, 12, 12,
            '[EANSIBLE0012] Commands should not change things if nothing needs doing'  # noqa
        )
        self.assertEqual(expected, problems[0])

        expected = Comment(
            fname, 18, 18,
            '[EANSIBLE0004] Git checkouts must contain explicit version'  # noqa
        )
        self.assertEqual(expected, problems[3])

    @requires_image('python2')
    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        self.assertEqual([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(11, len(problems))
        expected = Comment(
            self.fixtures[1], 12, 12,
            '[EANSIBLE0012] Commands should not change things if nothing needs doing'  # noqa
        )
        self.assertEqual(expected, problems[0])

        expected = Comment(
            self.fixtures[1], 27, 27,
            '[EANSIBLE0006] git used in place of git module'
        )
        self.assertEqual(expected, problems[5])

    @requires_image('python2')
    def test_config_options_and_process_file(self):
        options = {
            'ignore': 'ANSIBLE0012,ANSIBLE0006'
        }
        self.tool = Ansible(self.problems, options, root_dir)
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        self.assertEqual(7, len(problems))
        for p in problems:
            self.assertFalse('ANSIBLE0012' in p.body)
            self.assertFalse('ANSIBLE0006' in p.body)
