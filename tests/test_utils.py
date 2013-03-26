import lintreview.utils as utils
import os
from unittest import skipIf

js_hint_installed = os.path.exists(
    os.path.join(os.getcwd(), 'node_modules', '.bin', 'jshint'))


def test_in_path():
    assert utils.in_path('python'), 'No python in path'
    assert not utils.in_path('bad_cmd_name')


@skipIf(not js_hint_installed, 'Missing local jshint. Skipping')
def test_npm_exists():
    assert utils.npm_exists('jshint'), 'Should be there.'
    assert not utils.npm_exists('not there'), 'Should not be there.'
