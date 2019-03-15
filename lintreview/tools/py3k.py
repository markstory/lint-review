from __future__ import absolute_import

import logging

import lintreview.docker as docker
from lintreview.tools import stringify
from lintreview.tools.pylint import Pylint

log = logging.getLogger(__name__)


class Py3k(Pylint):
    """
    $ pylint --py3k is a special mode for porting to python 3 which
    disables other pylint checkers.
    see https://github.com/PyCQA/pylint/issues/761
    """

    name = 'py3k'
    accepted_options = ('ignore', )

    def check_dependencies(self):
        """
        See if python image is available
        """
        return docker.image_exists('python2')

    def make_command(self, files):
        self.check_options()

        command = self._base_command
        command.append('--py3k')

        if 'ignore' in self.options:
            command.extend(['-d', stringify(self.options['ignore'])])

        command.extend(files)
        return command
