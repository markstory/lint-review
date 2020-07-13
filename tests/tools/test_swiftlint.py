from unittest import TestCase
import os.path

from lintreview.review import Problems, Comment
from lintreview.tools.swiftlint import Swiftlint
from tests import root_dir, requires_image


FILE_WITH_NO_ERRORS = 'tests/fixtures/swiftlint/no_errors.swift',
FILE_WITH_ERRORS = 'tests/fixtures/swiftlint/has_errors.swift'


class TestSwiftlint(TestCase):

    def setUp(self):
        self.problems = Problems()
        options = {}
        self.tool = Swiftlint(self.problems, options, root_dir)

    def test_version(self):
        assert self.tool.version != ''

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.swift'))
        self.assertTrue(self.tool.match_file('dir/name/test.swift'))

    @requires_image('swiftlint')
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @requires_image('swiftlint')
    def test_process_files_pass(self):
        self.tool.process_files(FILE_WITH_NO_ERRORS)
        self.assertEqual([], self.problems.all(FILE_WITH_NO_ERRORS))

    @requires_image('swiftlint')
    def test_process_files_fail(self):
        self.tool.process_files([FILE_WITH_ERRORS])
        problems = self.problems.all(FILE_WITH_ERRORS)
        self.assertEqual(1, len(problems))

        msg = ("Colons should be next to the identifier when specifying "
               "a type and next to the key in dictionary literals.")
        expected = [Comment(FILE_WITH_ERRORS, 2, 2, msg)]
        self.assertEqual(expected, problems)

    @requires_image('swiftlint')
    def test_process_files_config_error(self):
        path = os.path.join(root_dir, 'tests', 'fixtures', 'swiftlint', 'bad_config')
        self.tool = Swiftlint(self.problems, {}, path)
        self.tool.process_files(['has_errors.swift'])
        problems = self.problems.all()
        self.assertEqual(2, len(problems))

        msg = (
            "Your `swiftlint` configuration generated warnings:"
            "\n"
            "```\n"
            "Invalid configuration for 'empty_count'. Falling back to default.\n"
            "```"
        )
        assert problems[0].body == msg
        assert "Colons should be next to the identifier" in problems[1].body
        assert problems[1].line == 2
