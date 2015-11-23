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


@celery.task(ignore_result=True)
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

    try:
        log.info('Loading pull request data from github. user=%s '
                 'repo=%s number=%s', user, repo, number)
        gh = github.get_repository(config, user, repo)
        pull_request = gh.pull_request(number)

        pr_dict = pull_request.as_dict()
        head_repo = pr_dict['head']['repo']['clone_url']
        private_repo = pr_dict['head']['repo']['private']
        pr_head = pr_dict['head']['sha']

        target_branch = pr_dict['base']['ref']
        if target_branch in review_config.ignore_branches():
            log.info('Pull request into ignored branch %s, skipping processing.' %
                     target_branch)
            return

        # Clone/Update repository
        target_path = git.get_repo_path(user, repo, number, config)
        git.clone_or_update(config, head_repo, target_path, pr_head,
                            private_repo)

        processor = Processor(gh, number, pr_head,
                              target_path, config)
        processor.load_changes()
        processor.run_tools(review_config)
        processor.publish()

        log.info('Completed lint processing for %s/%s/%s' % (
            user, repo, number))
    except BaseException, e:
        log.exception(e)


@celery.task(ignore_result=True)
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
