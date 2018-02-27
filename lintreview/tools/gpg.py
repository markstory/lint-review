from __future__ import absolute_import
import logging

import lintreview.docker as docker
from lintreview.review import IssueComment
from lintreview.tools import Tool

log = logging.getLogger(__name__)


class Gpg(Tool):

    name = 'gpg'

    def check_dependencies(self):
        """
        See if the gpg image exists
        """
        return docker.image_exists('gpg')

    def execute_commits(self, commits):
        """
        Check that HEAD commit has gpg signature
        """
        cmd = [
            'git', 'log', 'HEAD^..HEAD',
            '--show-signature', '--format=%H'
        ]

        output = docker.run('gpg', cmd, self.base_path)
        if 'Signature made' not in output:
            body = 'No gpg signature for tip of the branch.'
            self.problems.add(IssueComment(body))
