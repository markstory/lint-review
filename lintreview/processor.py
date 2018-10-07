from __future__ import absolute_import
import logging
import lintreview.tools as tools
import lintreview.fixers as fixers
from lintreview.diff import DiffCollection
from lintreview.fixers.error import ConfigurationError, WorkflowError
from lintreview.review import Problems, Review, IssueComment

log = logging.getLogger(__name__)


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
        self.problems = Problems()
        self._review = Review(repository, pull_request, config)

    def load_changes(self):
        log.info('Loading pull request patches from github.')
        files = self._pull_request.files()
        self._changes = DiffCollection(files)
        self.problems.set_changes(self._changes)

    def run_tools(self):
        if self._changes is None:
            raise RuntimeError('No loaded changes, cannot run tools. '
                               'Try calling load_changes first.')
        config = self._config

        files_to_check = self._changes.get_files(
            ignore_patterns=config.ignore_patterns()
        )
        commits_to_check = self._pull_request.commits()

        tool_list = tools.factory(
            config,
            self.problems,
            self._target_path)

        if config.fixers_enabled():
            self.apply_fixers(tool_list, files_to_check)

        tools.run(tool_list, files_to_check, commits_to_check)

    def apply_fixers(self, tool_list, files_to_check):
        try:
            fixer_context = fixers.create_context(
                self._config,
                self._target_path,
                self._repository,
                self._pull_request,
            )
            fixer_diff = fixers.run_fixers(
                tool_list,
                self._target_path,
                files_to_check)
            fixers.apply_fixer_diff(
                self._changes,
                fixer_diff,
                fixer_context)
        except (ConfigurationError, WorkflowError) as e:
            log.warn('Fixer application failed. Got %s', e)
            message = u'Unable to apply fixers. {}'.format(e)
            self.problems.add(IssueComment(message))
        except Exception as e:
            log.warn('Fixer application failed, '
                     'rolling back working tree. Got %s', e)
            fixers.rollback_changes(self._target_path)

    def publish(self, check_run_id=None):
        self.problems.limit_to_changes()
        if check_run_id:
            self._review.publish_checkrun(
                self.problems,
                check_run_id)
        else:
            self._review.publish_review(
                self.problems,
                self._pull_request.head)
