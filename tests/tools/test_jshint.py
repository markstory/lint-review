from lintreview.review import Review
from lintreview.tools.jshint import Jshint
from lintreview.utils import in_path
from unittest import TestCase
from unittest import skipIf

jshint_missing = not(in_path('jshint'))


class TestJshint(TestCase):

    def setUp(self):
        self.review = Review({})
        self.tool = Jshint(self.review)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('test.js'))
        self.assertTrue(self.tool.match_file('dir/name/test.js'))

    @skipIf(jshint_missing, 'Missing jshint, cannot run')
    def test_check_dependencies(self):
        self.assertTrue(self.tool.check_dependencies())
