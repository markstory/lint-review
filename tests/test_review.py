import json
import logging

from unittest import TestCase
from . import load_fixture
from lintreview.review import CodeReview
from lintreview.review import DiffCollection
from lintreview.review import Diff
from nose.tools import eq_

log = logging.getLogger(__name__)


class DiffCollectionCollection(TestCase):

    one_file = json.loads(
        load_fixture('one_file_pull_request.json'))

    two_files = json.loads(
        load_fixture('two_file_pull_request.json'))

    def test_create_one_element(self):
        changes = DiffCollection(self.one_file)
        eq_(1, len(changes))
        self.assert_instances(changes, 1, Diff)

    def test_create_two_files(self):
        changes = DiffCollection(self.two_files)
        eq_(2, len(changes))
        self.assert_instances(changes, 2, Diff)

    def test_get_files__one_file(self):
        changes = DiffCollection(self.one_file)
        result = changes.get_files()
        expected = [
            "View/Helper/AssetCompressHelper.php"
        ]
        eq_(expected, result)

    def test_get_files__two_files(self):
        changes = DiffCollection(self.two_files)
        result = changes.get_files()
        expected = [
            "Console/Command/Task/AssetBuildTask.php",
            "Test/test_files/View/Parse/single.ctp",
        ]
        eq_(expected, result)

    def assert_instances(self, collection, count, clazz):
        """
        Helper for checking a collection.
        """
        num = 0
        for item in collection:
            num += 1
            assert isinstance(item, clazz)
        eq_(count, num)


class TestDiff(TestCase):

    fixture = json.loads(
        load_fixture('one_file_pull_request.json'))

    def setUp(self):
        self.diff = Diff(self.fixture[0])

    def test_properties(self):
        eq_("View/Helper/AssetCompressHelper.php", self.diff.filename)
        expected = '7f73f381ad3284eeb5a23d3a451b5752c957054c'
        eq_(expected, self.diff.commit)

    def test_has_line_changed_added(self):
        pass


class TestCodeReview(TestCase):
    pass

