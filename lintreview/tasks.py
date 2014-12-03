import lintreview.github as github
import lintreview.git as git
import logging

from celery import Celery
from lintreview.config import load_config, get_lintrc_defaults
from lintreview.config import ReviewConfig
from lintreview.processor import Processor

config = load_config()
celery = Celery('lintreview.tasks')
celery.config_from_object(config)

log = logging.getLogger(__name__)


@celery.task(ignore_result=True, queue=config.get('TASK_QUEUE', None))
def process_pull_request(user, repo, number, lintrc):
    """
    Starts processing a pull request and running the various
    lint tools against it.
    """
    log.info('Starting to process lint for %s/%s/%s', user, repo, number)
    log.debug("lintrc contents '%s'", lintrc)
    lintrc_defaults = get_lintrc_defaults(config)
    review_config = ReviewConfig(lintrc, lintrc_defaults)

    if len(review_config.linters()) == 0:
        log.info('No configured linters, skipping processing.')
        return

    gh = github.get_client(config, user, repo)
    try:
        log.info('Loading pull request data from github.')
        pull_request = gh.pull_requests.get(number)
        head_repo = pull_request.head['repo']['clone_url']
        private_repo = pull_request.head['repo']['private']
        pr_head = pull_request.head['sha']

        # Clone/Update repository
        target_path = git.get_repo_path(user, repo, number, config)
        git.clone_or_update(config, head_repo, target_path, pr_head,
                            private_repo)

        processor = Processor(gh, number, pr_head, target_path, config)
        processor.load_changes()
        processor.run_tools(review_config)
        processor.publish()

        log.info('Completed lint processing for %s/%s/%s' % (
            user, repo, number))
    except BaseException, e:
        log.exception(e)


@celery.task(ignore_result=True, queue=config.get('TASK_QUEUE', None))
def cleanup_pull_request(user, repo, number):
    """
    Cleans up a pull request once its been closed.
    """
    log.info("Cleaning up pull request %s/%s/%s", user, repo, number)
    path = git.get_repo_path(user, repo, number, config)
    try:
        git.destroy(path)
    except:
        log.warning("Cannot cleanup '%s' path does not exist.", path)
