from __future__ import absolute_import
from unittest import TestCase
from lintreview.review import Problems
from lintreview.tools.gpg import Gpg
from nose.tools import eq_, assert_in
from tests import root_dir, requires_image


class TestGpg(TestCase):

    def setUp(self):
        self.problems = Problems()
        self.tool = Gpg(self.problems, {}, root_dir)

    @requires_image('gpg')
    def test_check_dependencies(self):
        eq_(True, self.tool.check_dependencies())

    @requires_image('gpg')
    def test_execute(self):
        self.tool.execute_commits([])

        comments = self.problems.all()
        if len(comments):
            assert_in('gpg signature', comments[0].body)
