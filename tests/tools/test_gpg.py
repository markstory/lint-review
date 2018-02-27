from __future__ import absolute_import
from unittest import TestCase
from lintreview.review import Problems
from lintreview.tools.gpg import Gpg, in_path
from nose.tools import eq_, assert_in


def test_in_path():
    assert in_path('python'), 'No python in path'
    assert not in_path('bad_cmd_name')


class TestGpg(TestCase):

    def setUp(self):
        self.problems = Problems()
        self.tool = Gpg(self.problems)

    def test_check_dependencies(self):
        eq_(True, self.tool.check_dependencies())

    def test_execute(self):
        self.tool.execute_commits([])

        comments = self.problems.all()
        if len(comments):
            assert_in('gpg signature', comments[0].body)
