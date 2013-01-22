from celery import Celery
from lintreview.utils.config import ReviewConfig
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

