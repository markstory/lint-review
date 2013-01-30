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

    # Single file, single commit
    one_file = json.loads(
        load_fixture('one_file_pull_request.json'))

    # Two files modified in the same commit
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

    def test_has_line_changed__no_file(self):
        changes = DiffCollection(self.two_files)
        assert False == changes.has_line_changed('derp', 99)

    def test_has_line_changed__no_line(self):
        changes = DiffCollection(self.two_files)
        assert False == changes.has_line_changed(
            'Console/Command/Task/AssetBuildTask.php',
            99999)

    def test_has_line_changed__two_files(self):
        changes = DiffCollection(self.two_files)
        filename = 'Console/Command/Task/AssetBuildTask.php'

        # True for additions
        assert True == changes.has_line_changed(filename, 117)
        assert True == changes.has_line_changed(filename, 119)

        # Should return false if the line was a deletion
        assert False == changes.has_line_changed(filename, 148)

        # Should return false for unchanged
        assert False == changes.has_line_changed(filename, 145)

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

    two_files = json.loads(
        load_fixture('two_file_pull_request.json'))

    def setUp(self):
        self.diff = Diff(self.fixture[0])

    def test_properties(self):
        eq_("View/Helper/AssetCompressHelper.php", self.diff.filename)
        expected = '7f73f381ad3284eeb5a23d3a451b5752c957054c'
        eq_(expected, self.diff.commit)

    def test_has_line_changed__no_line(self):
        assert False == self.diff.has_line_changed(None)

    def test_has_line_changed__added_only(self):
        # Check start and end of range
        assert True == self.diff.has_line_changed(454)
        assert True == self.diff.has_line_changed(464)

    def test_has_line_changed__not_find_deletes(self):
        diff = Diff(self.two_files[0])
        assert True == diff.has_line_changed(117)
        # No unchanged lines.
        assert False == diff.has_line_changed(118)
        assert True == diff.has_line_changed(119)
        # No deleted lines.
        assert False == diff.has_line_changed(148)


class TestCodeReview(TestCase):
    pass

