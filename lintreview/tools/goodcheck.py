from __future__ import absolute_import
import logging
import json
import lintreview.docker as docker
from lintreview.tools import Tool

log = logging.getLogger(__name__)


class Goodcheck(Tool):

    name = 'goodcheck'

    def check_dependencies(self):
        """
        See if ruby image exists
        """
        return docker.image_exists('ruby2')

    def process_files(self, files):
        """
        Run checks with goodcheck
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = self._create_command()
        command += files
        output = docker.run('ruby2', command, self.base_path)

        # The last line should contain a JSON document with results
        # from goodcheck
        self._process_output(output.strip().split("\n")[-1])

    def _create_command(self):
        command = ['goodcheck', 'check', '--format', 'json']
        if self.options.get('rules'):
            for rule in self.options['rules'].split(','):
                command.extend(['-R', rule.strip()])
        if self.options.get('config'):
            command.extend(['--config',
                            docker.apply_base(self.options['config'])])
        return command

    def _process_output(self, output):
        """
        Process goodcheck json results.

        Where `output` is a line containing check results, formatted like:
            [{"rule_id":"<id>","path":"<filename>",
              "location":{"start_line":<line>,"start_column":<col>,
                          "end_line":<endline>,"end_column":<endcol>},
              "message":"<message>",
              "justifications":[]}]
        """
        try:
            results = json.loads(output)
        except ValueError:
            log.debug('Failed to load JSON data from goodcheck output %r',
                      output)
            results = []

        for result in results:
            filename = docker.strip_base(result['path'])
            comment = result['message']

            add_justifications = self.options.get(
                'add_justifications_to_comments', False)
            if (result['justifications'] and add_justifications):
                comment += "\n\n - " + "\n - ".join(result['justifications'])

            self.problems.add(filename,
                              line=int(result['location']['start_line']),
                              body=comment)
