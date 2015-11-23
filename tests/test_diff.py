from . import load_fixture, create_pull_files
from lintreview.diff import DiffCollection
from lintreview.diff import Diff
from unittest import TestCase
from nose.tools import eq_


class TestDiffCollection(TestCase):

    # Single file, single commit
    one_file_json = load_fixture('one_file_pull_request.json')

    # Two files modified in the same commit
    two_files_json = load_fixture('two_file_pull_request.json')

    # Diff with renamed files
    renamed_files_json = load_fixture('diff_with_rename_and_blob.json')

    # Diff with removed files
    removed_files_json = load_fixture('diff_with_removed_files.json')

    def setUp(self):
        self.one_file = create_pull_files(self.one_file_json)
        self.two_files = create_pull_files(self.two_files_json)
        self.renamed_files = create_pull_files(self.renamed_files_json)
        self.removed_files = create_pull_files(self.renamed_files_json)

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

    def test_get_files__two_files__append_base(self):
        changes = DiffCollection(self.two_files)
        expected = [
            "/some/path/Console/Command/Task/AssetBuildTask.php",
            "/some/path/Test/test_files/View/Parse/single.ctp",
        ]
        result = changes.get_files(append_base="/some/path/")
        eq_(expected, result)

        result = changes.get_files(append_base="/some/path")
        eq_(expected, result)

    def test_get_files__two_files__ignore_pattern(self):
        changes = DiffCollection(self.two_files)
        expected = [
            "Console/Command/Task/AssetBuildTask.php",
        ]
        ignore = ['Test/**']
        result = changes.get_files(ignore_patterns=ignore)
        eq_(expected, result)

    def test_has_line_changed__no_file(self):
        changes = DiffCollection(self.two_files)
        self.assertFalse(changes.has_line_changed('derp', 99))

    def test_has_line_changed__no_line(self):
        changes = DiffCollection(self.two_files)
        self.assertFalse(changes.has_line_changed(
            'Console/Command/Task/AssetBuildTask.php',
            99999))

    def test_has_line_changed__two_files(self):
        changes = DiffCollection(self.two_files)
        filename = 'Console/Command/Task/AssetBuildTask.php'

        # True for additions
        self.assertTrue(changes.has_line_changed(filename, 117))
        self.assertTrue(changes.has_line_changed(filename, 119))

        # Should return false if the line was a deletion
        self.assertFalse(changes.has_line_changed(filename, 148))

        # Should return false for unchanged
        self.assertFalse(changes.has_line_changed(filename, 145))

    def test_parsing_diffs_removed__file(self):
        changes = DiffCollection(self.removed_files)
        eq_(0, len(changes), 'Should be no files as the file was removed')
        eq_([], changes.get_files())

    def test_parsing_diffs__renamed_file_and_blob(self):
        changes = DiffCollection(self.renamed_files)
        eq_(0, len(changes), 'Should be no files as a blob and a rename happened')
        eq_([], changes.get_files())

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

    fixture_json = load_fixture('one_file_pull_request.json')
    two_files_json = load_fixture('two_file_pull_request.json')

    # Block offset so lines don't match offsets
    block_offset = load_fixture('pull_request_line_offset.json')

    def setUp(self):
        res = create_pull_files(self.fixture_json)
        self.diff = Diff(res[0])

    def test_properties(self):
        eq_("View/Helper/AssetCompressHelper.php", self.diff.filename)
        expected = '7f73f381ad3284eeb5a23d3a451b5752c957054c'
        eq_(expected, self.diff.commit)

    def test_has_line_changed__no_line(self):
        self.assertFalse(self.diff.has_line_changed(None))

    def test_has_line_changed__added_only(self):
        # Check start and end of range
        self.assertTrue(self.diff.has_line_changed(454))
        self.assertTrue(self.diff.has_line_changed(464))

    def test_has_line_changed__not_find_deletes(self):
        res = create_pull_files(self.two_files_json)
        diff = Diff(res[0])

        self.assertTrue(diff.has_line_changed(117))
        # No unchanged lines.
        self.assertFalse(diff.has_line_changed(118))
        self.assertTrue(diff.has_line_changed(119))
        # No deleted lines.
        self.assertFalse(diff.has_line_changed(148))

    def test_has_line_changed__blocks_offset(self):
        res = create_pull_files(self.block_offset)
        diff = Diff(res[0])

        self.assertTrue(diff.has_line_changed(32))
        eq_(26, diff.line_position(23))
        eq_(40, diff.line_position(32))
