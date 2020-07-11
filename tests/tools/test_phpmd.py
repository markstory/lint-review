from lintreview.review import Problems
from lintreview.tools.phpmd import Phpmd
from unittest import TestCase
from tests import root_dir, requires_image


class TestPhpmd(TestCase):

    fixtures = [
        'tests/fixtures/phpmd/no_errors.php',
        'tests/fixtures/phpmd/has_errors.php',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Phpmd(self.problems, base_path=root_dir)

    def test_version(self):
        assert self.tool.version != ''

    def test_match_file(self):
        self.assertTrue(self.tool.match_file('test.php'))
        self.assertTrue(self.tool.match_file('dir/name/test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertFalse(self.tool.match_file('test.js'))

    @requires_image('php')
    def test_check_dependencies(self):
        assert self.tool.check_dependencies()

    @requires_image('php')
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        assert len(self.problems) == 0

    @requires_image('php')
    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])

        errors = self.problems.all(self.fixtures[1])
        assert len(errors) == 1

        error = errors[0]
        assert 7 == error.line
        assert 'CyclomaticComplexity:' in error.body
        assert 'The method tooComplex()' in error.body
        assert 'See: https://phpmd.org/' in error.body

    @requires_image('php')
    def test_process_files__two_files(self):
        self.tool.process_files(self.fixtures)

        errors = self.problems.all(self.fixtures[0])
        assert len(errors) == 0

        errors = self.problems.all(self.fixtures[1])
        assert len(errors) == 1

    @requires_image('php')
    def test_process_files__invalid_ruleset(self):
        tool = Phpmd(self.problems, {'ruleset': 'garbage'}, base_path=root_dir)
        tool.process_files(self.fixtures)

        errors = self.problems.all()
        assert len(errors) == 1
        assert 'PHPMD configuration output the following error:' in errors[0].body
        assert 'Cannot find specified rule-set "garbage"' in errors[0].body
