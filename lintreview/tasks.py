import lintreview.git as git
import logging

from celery import Celery
from copy import deepcopy
from lintreview.config import load_config, build_review_config
from lintreview.repo import GithubRepository
from lintreview.processor import Processor
from lintreview.docker import TimeoutError

config = load_config()
celery = Celery('lintreview.tasks')
celery.config_from_object(config)

log = logging.getLogger(__name__)


@celery.task(bind=True, ignore_result=True)
def process_pull_request(self, user, repo_name, number, lintrc):
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
        review, problems = processor.execute()
        review.publish(problems)

        log.info('Completed lint processing for %s/%s/%s' % (
            user, repo_name, number))

    except Exception as e:
        log.exception(e)
    except TimeoutError as e:
        log.exception(e)
        raise self.retry(
            countdown=5,  # Pause for 5 seconds to clear things out
            max_retries=2,  # only give it one more shot
        )
    finally:
        try:
            git.destroy(target_path)
            log.info('Cleaned up pull request %s/%s/%s',
                     user, repo_name, number)
        except Exception as e:
            log.exception(e)
