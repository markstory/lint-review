import celery
import logging

log = logging.getLogger(__name__)


@celery.task()
def process_pull_request(user, repo, number, lintrc):
    log.info('Got a job!')
