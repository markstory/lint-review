import logging

from flask import Flask, request, Response
from lintreview.config import load_config
from lintreview.github import get_client
from lintreview.github import get_lintrc
from lintreview.tasks import process_pull_request
from lintreview.tasks import cleanup_pull_request

config = load_config()
app = Flask("lintreview")
app.config.update(config)

log = logging.getLogger(__name__)


@app.route("/ping")
def ping():
    return "pong\n"


@app.route("/review/start", methods=["POST"])
def start_review():
    try:
        action = request.json["action"]
        pull_request = request.json["pull_request"]
        number = pull_request["number"]
        base_repo_url = pull_request["base"]["repo"]["git_url"]
        head_repo_url = pull_request["head"]["repo"]["git_url"]
        user = pull_request["base"]["repo"]["owner"]["login"]
        repo = pull_request["base"]["repo"]["name"]
    except Exception as e:
        log.error("Got an invalid JSON body. '%s'", e)
        return Response(status=403,
                        response="You must provide a valid JSON body\n")

    log.debug("Received GitHub pull request notification for "
              "%s %s, (%s) from: %s",
              base_repo_url, number, action, head_repo_url)

    if action not in ("opened", "synchronize", "closed"):
        log.info("Ignored '%s' action." % action)
        return Response(status=204)

    if action == "closed":
        try:
            log.info("Scheduling cleanup for %s/%s", user, repo)
            cleanup_pull_request.delay(user, repo, pull_request['number'])
        except:
            log.error('Could not publish job to celery. '
                      'Make sure its running.')
        return Response(status=204)

    gh = get_client(app.config, user, repo)
    try:
        lintrc = get_lintrc(gh)
        log.debug("lintrc file contents '%s'", lintrc)
    except:
        log.warn("Cannot download .lintrc file for '%s', "
                 "skipping lint checks.", base_repo_url)
        return Response(status=204)
    try:
        log.info("Scheduling pull request for %s/%s %s", user, repo, number)
        process_pull_request.delay(user, repo, number, lintrc)
    except:
        log.error('Could not publish job to celery. Make sure its running')
        return Response(status=500)
    return Response(status=204)


if __name__ == '__main__':
    app.run()
