from __future__ import absolute_import
import lintreview.git as git
import logging

from celery import Celery
from copy import deepcopy
from lintreview.config import load_config, build_review_config
from lintreview.repo import GithubRepository
from lintreview.processor import Processor

config = load_config()
celery = Celery('lintreview.tasks')
celery.config_from_object(config)

log = logging.getLogger(__name__)


@celery.task(ignore_result=True)
def process_pull_request(user, repo_name, number, lintrc):
    """
    Starts processing a pull request and running the various
    lint tools against it.
    """
    log.info('Starting to process lint for %s/%s/%s', user, repo_name, number)
    log.debug("lintrc contents '%s'", lintrc)
    review_config = build_review_config(lintrc, deepcopy(config))

    if len(review_config.linters()) == 0:
        log.info('No configured linters, skipping processing.')
        return

    try:
        log.info('Loading pull request data from github. user=%s '
                 'repo=%s number=%s', user, repo_name, number)
        repo = GithubRepository(config, user, repo_name)
        pull_request = repo.pull_request(number)

        clone_url = pull_request.clone_url

        pr_head = pull_request.head
        target_branch = pull_request.target_branch

        if target_branch in review_config.ignore_branches():
            log.info('Pull request into ignored branch %s, skipping review.',
                     target_branch)
            return

        repo.create_status(pr_head, 'pending', 'Lintreview processing')

        # Clone/Update repository
        target_path = git.get_repo_path(user, repo_name, number, config)
        git.clone_or_update(config, clone_url, target_path, pr_head)

        processor = Processor(repo, pull_request, target_path, review_config)
        processor.load_changes()
        processor.run_tools()
        processor.publish()

        log.info('Completed lint processing for %s/%s/%s' % (
            user, repo_name, number))

    except BaseException as e:
        log.exception(e)
    finally:
        try:
            git.destroy(target_path)
            log.info('Cleaned up pull request %s/%s/%s',
                     user, repo_name, number)
        except BaseException as e:
            log.exception(e)


@celery.task(ignore_result=True)
def cleanup_pull_request(user, repo, number):
    """
    No-op for backwards compat.
    """
    log.info("Doing nothing cleanup happens after review now.")
