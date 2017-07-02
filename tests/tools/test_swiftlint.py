from unittest import TestCase
from unittest import skipIf

from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.tools.swiftlint import Swiftlint
from lintreview.utils import in_path
from nose.tools import eq_

swiftlint_missing = not in_path('swiftlint')

FILE_WITH_NO_ERRORS = 'tests/fixtures/swiftlint/no_errors.swift',
FILE_WITH_ERRORS = 'tests/fixtures/swiftlint/has_errors.swift'


class TestSwiftlint(TestCase):

    needs_swiftlint = skipIf(swiftlint_missing, 'Needs swiftlint to run')

    def setUp(self):
        self.problems = Problems()
        options = {}
        self.tool = Swiftlint(self.problems, options)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.swift'))
        self.assertTrue(self.tool.match_file('dir/name/test.swift'))

    @needs_swiftlint
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())

    @needs_swiftlint
    def test_process_files_pass(self):
        self.tool.process_files(FILE_WITH_NO_ERRORS)
        eq_([], self.problems.all(FILE_WITH_NO_ERRORS))

    @needs_swiftlint
    def test_process_files_fail(self):
        self.tool.process_files([FILE_WITH_ERRORS])
        problems = self.problems.all(FILE_WITH_ERRORS)
        eq_(1, len(problems))

        msg = ("Colons should be next to the identifier when specifying "
               "a type and next to the key in dictionary literals.")
        expected = [Comment(FILE_WITH_ERRORS, 2, 2, msg)]
        eq_(expected, problems)
