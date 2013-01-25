import json

from unittest import TestCase
from . import load_fixture
from lintreview.review import CodeReview
from lintreview.review import ChangeCollection
from lintreview.review import ChangedFile
from nose.tools import eq_


class TestChangeCollection(TestCase):

    def create_one_element(self):
        fixture = json.loads(load_fixture(
            'basic_pull_request.json'))
        changes = ChangeCollection(fixture)
        eq_(1, len(changes))

        num = 0
        for change in changes:
            num += 1
            assert isinstance(change, ChangedFile)
        eq_(1, num)


class TestChangedFile(TestCase):
    pass

class TestCodeReview(TestCase):
    pass

