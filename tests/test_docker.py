from __future__ import absolute_import
from unittest import TestCase

import lintreview.docker as docker
from tests import test_dir, requires_image


class TestDocker(TestCase):

    def test_replace_basedir(self):
        files = ['/tmp/things/some/thing.py', 'some/other.py']
        out = docker.replace_basedir('/tmp/things', files)
        expected = ['/src/some/thing.py', '/src/some/other.py']
        self.assertEqual(expected, out)

    def test_strip_base(self):
        self.assertEqual('some/thing.py',
                         docker.strip_base('/src/some/thing.py'))
        self.assertEqual('some/thing.py', docker.strip_base('some/thing.py'))
        self.assertEqual('some/src/thing.py',
                         docker.strip_base('some/src/thing.py'))

    def test_apply_base(self):
        self.assertEqual('/src', docker.apply_base(''))
        self.assertEqual('/src', docker.apply_base('/'))
        self.assertEqual('/src/thing.py', docker.apply_base('thing.py'))
        self.assertEqual('/src/some/thing.py',
                         docker.apply_base('some/thing.py'))
        self.assertEqual('thing.py', docker.apply_base('/some/thing.py'))
        self.assertEqual('thing.py', docker.apply_base('/some/../../thing.py'))

    @requires_image('python2')
    def test_run__unicode(self):
        cmd = ['echo', "\u2620"]
        output = docker.run('python2', cmd, test_dir)
        self.assertEqual(output, "\u2620\n")

    @requires_image('python2')
    def test_run__named_container(self):
        cmd = ['echo', "things"]
        docker.run('python2', cmd, test_dir, name='test_container')
        containers = docker.containers(include_stopped=True)
        self.assertIn('test_container', containers)
        docker.rm_container('test_container')

        containers = docker.containers(include_stopped=True)
        assert 'test_conainer' not in containers

    @requires_image('python2')
    def test_images(self):
        result = docker.images()
        self.assertIn('python2', result)
