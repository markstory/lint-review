import logging

import lintreview.git as git
import lintreview.fixers as fixers
import lintreview.tools as tools
from lintreview.diff import DiffCollection, parse_diff
from lintreview.fixers.error import ConfigurationError, WorkflowError
from lintreview.review import Problems, Review, IssueComment, InfoComment

log = logging.getLogger(__name__)
buildlog = logging.getLogger('buildlog')


class Processor(object):

    _repository = None
    _pull_request = None
    _target_path = None
    _changes = None
    _review = None
    _config = None
    problems = None

    def __init__(self, repository, pull_request, target_path, config):
        self._config = config
        self._repository = repository
        self._pull_request = pull_request
        self._target_path = target_path
        # TODO move problems into the Review
        # so that it is more self contained.
        self.problems = Problems()
        self._review = Review(repository, pull_request, config)

    def load_changes(self):
        log.debug('Loading pull request patches from github.')
        files = self._pull_request.files()
        self._changes = DiffCollection(files)
        self.problems.set_changes(self._changes)

    def parse_local_changes(self):
        head = self._pull_request.head
        base = self._pull_request.base

        diff_text = git.diff_commit_range(self._target_path, base, head)
        return parse_diff(diff_text)

    def parse_changes(self):
        self._changes = self.parse_local_changes()
        self.problems.set_changes(self._changes)

    def execute(self):
        """
        Run the review and return the completed review.

        Return the review object and collected problems
        """
        self.run_tools()
        return (self._review, self.problems)

    def run_tools(self):
        """
        Run linters on the changed files, collecting
        results into the review.

        - Build the list of tools to run
        - Run fixer mode of tools that support it.
        - Run linter mode of each tool.
        """
        if self._changes is None:
            raise RuntimeError('No loaded changes, cannot run tools. '
                               'Try calling load_changes first.')
        config = self._config

        files_to_check = self._changes.get_files(
            ignore_patterns=config.ignore_patterns()
        )
        commits_to_check = self._pull_request.commits()

        try:
            tool_list = tools.factory(
                config,
                self.problems,
                self._target_path)
        except Exception as e:
            msg = (
                u'We could not load linters for your repository. '
                'Building linters failed with:'
                '\n'
                '```\n'
                '{}\n'
                '```\n'
            )
            self.problems.add(IssueComment(msg.format(str(e))))
            return

        if config.fixers_enabled():
            self.apply_fixers(tool_list, files_to_check)

        tools.run(tool_list, files_to_check, commits_to_check)

    def apply_fixers(self, tool_list, files_to_check):
        fixer_context = fixers.create_context(
            self._config,
            self._target_path,
            self._repository,
            self._pull_request,
        )
        if not fixers.should_run(fixer_context):
            buildlog.info('Did not run fixers as HEAD commit is from {}'.format(
                fixer_context['author_email']
            ))
            return
        try:
            fixer_diff = fixers.run_fixers(
                tool_list,
                self._target_path,
                files_to_check)
            fixers.apply_fixer_diff(
                self._changes,
                fixer_diff,
                fixer_context)
        except (ConfigurationError, WorkflowError) as e:
            log.info('Fixer application failed. Got %s', e)
            message = u'Unable to apply fixers. {}'.format(e)
            self.problems.add(InfoComment(message))
            fixers.rollback_changes(self._target_path, self._pull_request.head)
        except Exception as e:
            log.info('Fixer application failed, '
                     'rolling back working tree. Got %s', e)
            fixers.rollback_changes(self._target_path, self._pull_request.head)
