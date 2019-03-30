from __future__ import absolute_import
from . import load_fixture, create_pull_files
from lintreview.diff import DiffCollection, Diff, parse_diff, ParseError
from unittest import TestCase
from mock import patch
import re


class TestDiffCollection(TestCase):

    # Single file, single commit
    one_file_json = load_fixture('one_file_pull_request.json')

    # Two files modified in the same commit
    two_files_json = load_fixture('two_file_pull_request.json')

    # Diff with renamed files
    renamed_files_json = load_fixture('diff_with_rename_and_blob.json')

    # Diff with removed files
    removed_files_json = load_fixture('diff_with_removed_files.json')

    single_line_add_json = load_fixture('diff_single_line_add.json')

    def setUp(self):
        self.one_file = create_pull_files(self.one_file_json)
        self.two_files = create_pull_files(self.two_files_json)
        self.renamed_files = create_pull_files(self.renamed_files_json)
        self.removed_files = create_pull_files(self.renamed_files_json)

    def test_create_one_element(self):
        changes = DiffCollection(self.one_file)
        self.assertEqual(1, len(changes))
        self.assert_instances(changes, 1, Diff)

    def test_create_two_files(self):
        changes = DiffCollection(self.two_files)
        self.assertEqual(2, len(changes))
        self.assert_instances(changes, 2, Diff)

    def test_get_files__one_file(self):
        changes = DiffCollection(self.one_file)
        result = changes.get_files()
        expected = [
            "View/Helper/AssetCompressHelper.php"
        ]
        self.assertEqual(expected, result)

    def test_get_files__two_files(self):
        changes = DiffCollection(self.two_files)
        result = changes.get_files()
        expected = [
            "Console/Command/Task/AssetBuildTask.php",
            "Test/test_files/View/Parse/single.ctp",
        ]
        self.assertEqual(expected, result)

    def test_get_files__two_files__ignore_pattern(self):
        changes = DiffCollection(self.two_files)
        expected = [
            "Console/Command/Task/AssetBuildTask.php",
        ]
        ignore = ['Test/**']
        result = changes.get_files(ignore_patterns=ignore)
        self.assertEqual(expected, result)

    def test_get_files__ignore_pattern__multiple_wildcard(self):
        data = load_fixture('multiple_wildcard_pull_request.json')
        changes = DiffCollection(create_pull_files(data))
        expected = [
            "buildpacks/buildpack-ruby/tests/ruby-sinatra/test_web.rb",
        ]
        ignore = ['buildpacks/*/tests/*/test.sh']
        result = changes.get_files(ignore_patterns=ignore)
        self.assertEqual(expected, result)

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

    def test_has_line_changed__single_line(self):
        filename = 'some.js'
        pull_file = create_pull_files(self.single_line_add_json)
        changes = DiffCollection(pull_file)

        self.assertTrue(changes.has_line_changed(filename, 1))
        self.assertFalse(changes.has_line_changed(filename, 0))
        self.assertFalse(changes.has_line_changed(filename, 2))

    def test_parsing_diffs_removed__file(self):
        changes = DiffCollection(self.removed_files)
        self.assertEqual(0, len(changes),
                         'Should be no files as the file was removed')
        self.assertEqual([], changes.get_files())

    def test_parsing_diffs__renamed_file_and_blob(self):
        changes = DiffCollection(self.renamed_files)
        self.assertEqual(0, len(changes),
                         'Should be no files as a blob and a rename happened')
        self.assertEqual([], changes.get_files())

    @patch('lintreview.diff.log')
    def test_parsing_diffs__renamed_file_and_blob_no_log(self, log):
        DiffCollection(self.renamed_files)
        self.assertEqual(False, log.warn.called)
        self.assertEqual(False, log.error.called)

    def assert_instances(self, collection, count, clazz):
        """
        Helper for checking a collection.
        """
        num = 0
        for item in collection:
            num += 1
            assert isinstance(item, clazz)
        self.assertEqual(count, num)


class TestDiff(TestCase):

    fixture_json = load_fixture('one_file_pull_request.json')
    two_files_json = load_fixture('two_file_pull_request.json')

    # Block offset so lines don't match offsets
    block_offset = load_fixture('pull_request_line_offset.json')

    def setUp(self):
        res = create_pull_files(self.fixture_json)
        self.diff = Diff(res[0].patch, res[0].filename, res[0].sha)

    def test_parse_diff__no_input(self):
        with self.assertRaises(ParseError) as ctx:
            parse_diff('')
        self.assertIn('No diff', str(ctx.exception))

    def test_parse_diff__headers_removed(self):
        data = load_fixture('diff/one_file.txt')
        out = parse_diff(data)

        assert isinstance(out, DiffCollection)
        self.assertEqual(1, len(out))
        self.assertEqual(['tests/test_diff.py'], out.get_files())

        change = out.all_changes('tests/test_diff.py')
        self.assertEqual(1, len(change))
        self.assertEqual('tests/test_diff.py', change[0].filename)
        self.assertEqual(None, change[0].commit,
                         'No commit as changes are just a diff')

        # Make sure git diff headers are not in patch
        self.assertNotIn('git --diff', change[0].patch)
        self.assertNotIn('index', change[0].patch)
        self.assertNotIn('--- a', change[0].patch)
        self.assertNotIn('+++ b', change[0].patch)
        self.assertIn('@@', change[0].patch)

    def test_parse_diff__changed_lines_parsed(self):
        data = load_fixture('diff/one_file.txt')
        out = parse_diff(data)

        assert isinstance(out, DiffCollection)
        change = out.all_changes('tests/test_diff.py')
        self.assertEqual(1, len(change))

        expected = set([6, 9, 10, 55])
        self.assertEqual(expected, change[0].deleted_lines())

    def test_parse_diff__multiple_files(self):
        data = load_fixture('diff/two_files.txt')
        out = parse_diff(data)
        self.assertEqual(2, len(out))
        self.assertEqual(['lintreview/git.py', 'tests/test_git.py'],
                         out.get_files())

        for change in out:
            assert change.filename, 'has a filename'
            assert change.commit is None, 'No commit'
            self.assertNotIn('git --diff', change.patch)
            self.assertNotIn('index', change.patch)
            self.assertNotIn('--- a', change.patch)
            self.assertNotIn('+++ b', change.patch)
            self.assertIn('@@', change.patch)
        change = out.all_changes('tests/test_git.py')[0]
        self.assertEqual({205, 206, 207, 208, 209, 210, 211, 212, 213},
                         change.added_lines())

    def test_parse_diff__bad_input(self):
        data = """
        some dumb stuff
        """
        with self.assertRaises(ParseError) as ctx:
            parse_diff(data)
        self.assertIn('Could not parse', str(ctx.exception))

    def test_properties(self):
        self.assertEqual("View/Helper/AssetCompressHelper.php",
                         self.diff.filename)
        expected = '7f73f381ad3284eeb5a23d3a451b5752c957054c'
        self.assertEqual(expected, self.diff.commit)

    def test_patch_property(self):
        res = create_pull_files(self.two_files_json)
        diff = Diff(res[0].patch, res[0].filename, res[0].sha)

        self.assertEqual(res[0].patch, diff.patch)

    def test_as_diff__one_hunk(self):
        data = load_fixture('diff/no_intersect_updated.txt')
        diff = parse_diff(data)[0]
        # Method results don't include index line.
        data = re.sub(r'^index.*?\n', '', data, 0, re.M)
        self.assertEqual(data, diff.as_diff())

    def test_as_diff__multi_hunk(self):
        data = load_fixture('diff/inset_hunks_updated.txt')
        diff = parse_diff(data)[0]
        # Method results don't include index line.
        data = re.sub(r'^index.*?\n', '', data, 0, re.M)
        self.assertEqual(data, diff.as_diff())

    def test_has_line_changed__no_line(self):
        self.assertFalse(self.diff.has_line_changed(None))

    def test_has_line_changed__added_only(self):
        # Check start and end of range
        self.assertTrue(self.diff.has_line_changed(454))
        self.assertTrue(self.diff.has_line_changed(464))

    def test_has_line_changed__not_find_deletes(self):
        res = create_pull_files(self.two_files_json)
        diff = Diff(res[0].patch, res[0].filename, res[0].sha)

        self.assertTrue(diff.has_line_changed(117))
        # No unchanged lines.
        self.assertFalse(diff.has_line_changed(118))
        self.assertTrue(diff.has_line_changed(119))
        # No deleted lines.
        self.assertFalse(diff.has_line_changed(147))
        self.assertFalse(diff.has_line_changed(148))

    def test_has_line_changed__blocks_offset(self):
        res = create_pull_files(self.block_offset)
        diff = Diff(res[0].patch, res[0].filename, res[0].sha)

        self.assertTrue(diff.has_line_changed(32))
        self.assertEqual(26, diff.line_position(23))
        self.assertEqual(40, diff.line_position(32))

    def test_added_lines(self):
        res = create_pull_files(self.two_files_json)
        diff = Diff(res[0].patch, res[0].filename, res[0].sha)

        adds = diff.added_lines()
        self.assertEqual(2, len(adds), 'incorrect addition length')
        self.assertEqual(set([117, 119]), adds, 'added line numbers are wrong')

    def test_deleted_lines(self):
        res = create_pull_files(self.two_files_json)
        diff = Diff(res[0].patch, res[0].filename, res[0].sha)

        dels = diff.deleted_lines()
        self.assertEqual(3, len(dels), 'incorrect deleted length')
        self.assertEqual(set([117, 119, 148]), dels,
                         'deleted line numbers are wrong')

        overlap = diff.added_lines().intersection(diff.deleted_lines())
        self.assertEqual(set([117, 119]), overlap)

    def test_hunk_parsing(self):
        res = create_pull_files(self.two_files_json)
        diff = Diff(res[0].patch, res[0].filename, res[0].sha)

        hunks = diff.hunks
        self.assertEqual(2, len(hunks))

        expected = set([117, 119])
        self.assertEqual(expected, hunks[0].added_lines())
        self.assertEqual(expected, hunks[0].deleted_lines())
        self.assertEqual(expected, diff.added_lines())

        self.assertEqual(set([]), hunks[1].added_lines())
        self.assertEqual(set([148]), hunks[1].deleted_lines())
        self.assertEqual(set([117, 119, 148]), diff.deleted_lines())

        self.assertEqual(diff.line_position(117), hunks[0].line_position(117))
        self.assertEqual(diff.line_position(119), hunks[0].line_position(119))

    def test_construct_with_hunks_kwarg(self):
        res = create_pull_files(self.two_files_json)[0]
        proto = Diff(res.patch, res.filename, res.sha)

        diff = Diff(None, res.filename, res.sha, hunks=proto.hunks)
        self.assertEqual(len(diff.hunks), len(proto.hunks))
        self.assertEqual(diff.hunks[0].patch, proto.hunks[0].patch)

    def test_construct_with_empty_hunks_kwarg(self):
        diff = Diff(None, 'test.py', 'abc123', hunks=[])
        self.assertEqual(0, len(diff.hunks))

    def test_intersection__simple(self):
        # These two diffs should fully overlap as
        # the updated diff hunks touch the original hunks.
        original = load_fixture('diff/intersecting_hunks_original.txt')
        updated = load_fixture('diff/intersecting_hunks_updated.txt')

        original = parse_diff(original)[0]
        updated = parse_diff(updated)[0]
        intersecting = updated.intersection(original)
        self.assertEqual(4, len(updated.hunks))
        self.assertEqual(4, len(intersecting))

    def test_intersection__no_intersect(self):
        # Diffs have no overlap as updated appends lines.
        original = load_fixture('diff/no_intersect_original.txt')
        updated = load_fixture('diff/no_intersect_updated.txt')

        original = parse_diff(original)[0]
        updated = parse_diff(updated)[0]
        intersecting = updated.intersection(original)
        self.assertEqual(1, len(updated.hunks))
        self.assertEqual(0, len(intersecting))

    def test_intersection__inset_hunks(self):
        # Updated contains two hunks inside original's changes
        original = load_fixture('diff/inset_hunks_original.txt')
        updated = load_fixture('diff/inset_hunks_updated.txt')

        original = parse_diff(original)[0]
        updated = parse_diff(updated)[0]
        intersecting = updated.intersection(original)
        self.assertEqual(2, len(updated.hunks))
        self.assertEqual(2, len(intersecting))

    def test_intersection__staggered_hunks(self):
        # Updated contains a big hunk in the middle that pushes
        # the original section down. The bottom hunk of updated
        # should overlap
        original = load_fixture('diff/staggered_original.txt')
        updated = load_fixture('diff/staggered_updated.txt')

        original = parse_diff(original)[0]
        updated = parse_diff(updated)[0]
        intersecting = updated.intersection(original)
        self.assertEqual(2, len(updated.hunks))
        self.assertEqual(2, len(intersecting))

    def test_intersection__adjacent(self):
        # Updated contains a two hunks that partially overlap
        # both should be included.
        original = load_fixture('diff/adjacent_original.txt')
        updated = load_fixture('diff/adjacent_updated.txt')

        original = parse_diff(original)[0]
        updated = parse_diff(updated)[0]
        intersecting = updated.intersection(original)
        self.assertEqual(2, len(intersecting))
