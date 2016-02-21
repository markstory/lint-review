import logging
import lintreview.tools as tools

from lintreview.diff import DiffCollection
from lintreview.review import Problems
from lintreview.review import Review

log = logging.getLogger(__name__)


class Processor(object):

    _repository = None
    _pull_request = None
    _target_path = None
    _changes = None
    _problems = None
    _review = None
    _config = None

    def __init__(self, repository, pull_request, target_path, config=None):
        config = config if config else {}
        self._config = config
        self._repository = repository
        self._pull_request = pull_request
        self._target_path = target_path
        self._problems = Problems(target_path)
        self._review = Review(repository, pull_request, config)

    def load_changes(self):
        log.info('Loading pull request patches from github.')
        files = self._pull_request.files()
        self._changes = DiffCollection(files)
        self._problems.set_changes(self._changes)

    def run_tools(self, review_config):
        if self._changes is None:
            raise RuntimeError('No loaded changes, cannot run tools. '
                               'Try calling load_changes first.')
        files_to_check = self._changes.get_files(
            append_base=self._target_path,
            ignore_patterns=review_config.ignore_patterns())
        commits_to_check = self._pull_request.commits()
        tools.run(
            review_config,
            self._problems,
            files_to_check,
            commits_to_check,
            self._target_path)

    def publish(self):
        self._problems.limit_to_changes()
        self._review.publish(
            self._problems,
            self._pull_request.head,
            self._config.get('SUMMARY_THRESHOLD'))
