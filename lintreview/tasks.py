from celery import Celery
import lintreview.github as github
from lintreview.utils.config import load_settings
from lintreview.utils.config import ReviewConfig
from lintreview.review import DiffCollection
from lintreview.review import Review
import lintreview.tools as tools
import logging

celery = Celery('lintreview.tasks')
log = logging.getLogger(__name__)


@celery.task(ignore_result=True)
def process_pull_request(user, repo, number, lintrc):
    """
    Starts processing a pull request and running the various
    lint tools against it.
    """
    log.info('Starting to process lint for %s, %s, %s', user, repo, number)
    config = ReviewConfig(lintrc)

    settings = load_settings()

    gh = github.get_client(settings, user, repo)
    try:
        log.debug('Loading pull request data from github.')
        pull_request = gh.pull_requests.get(number)
        head_repo = pull_request['head']['repo']['git_url']
        pr_head = pull_request['head']['sha']

        # Clone repository
        log.info("Cloning repository '%s' into '%s'",
            head_repo, settings['WORKSPACE'])

        # Check out new head
        log.info("Checking out '%s'", pr_head)

        # Get changed files.
        log.debug('Loading pull request patches from github.')
        pull_request_patches = gh.pull_requests.list_files(number).all()
        changes = DiffCollection(pull_request_patches)

        #TODO add workspace path here, so the review
        # can chop it off when tracking problems?
        review = Review(gh)

        log.debug('Generating tool list from repository configuration')
        lint_tools = tools.factory(review, config)

        #TODO Add workspace clone path to files.
        files_to_check = changes.get_files()

        log.debug('Running lint tools on changed files.')
        for tool in lint_tools:
            tool.process_files(files_to_check)

        log.debug('Publishing review to github.')
        review.publish()

        log.info('Completed lint processing for %s, %s, %s' % (
            user, repo, number))
    except BaseException, e:
        log.exception(e)


if __name__ == '__main__':
    import sys
    process_pull_request(*sys.argv)
