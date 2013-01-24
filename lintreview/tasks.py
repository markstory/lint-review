from celery import Celery
import lintreview.github as github
from lintreview.utils.config import load_settings, ReviewConfig
from lintreview.review import CodeReview
import logging

celery = Celery('lintreview.tasks')
log = logging.getLogger(__name__)


@celery.task(ignore_result=True)
def process_pull_request(user, repo, number, lintrc):
    """
    Starts processing a pull request and running the various
    lint tools against it.
    """
    log.info('Starting to process lint for %s, %s, %s' % (user, repo, number))
    config = ReviewConfig(lintrc)

    gh = github.get_client(load_settings(), user, repo)
    try:
        pull_request = gh.pull_requests.get(number)
        review = CodeReview(config, gh, pull_request)
        review.run()
        log.info('Completed lint processing for %s, %s, %s' % (
            user, repo, number))
    except BaseException, e:
        log.exception(e)


if __name__ == '__main__':
    import sys
    process_pull_request(*sys.argv)
