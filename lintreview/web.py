import logging
import os

from flask import Flask, request, Response
from .github import get_client, get_lintrc

app = Flask('lintreview')

app.config.from_object('lintreview.default_settings')

if 'LINTREVIEW_SETTINGS' in os.environ:
    app.config.from_envvar('LINTREVIEW_SETTINGS')

log = logging.getLogger(__name__)


@app.route('/ping')
def ping():
    return 'pong\n'


@app.route('/review/start', methods=['POST'])
def start_review():
    action = request.json["action"]
    pull_request = request.json["pull_request"]
    number = pull_request["number"]
    base_repo_url = pull_request["base"]["repo"]["git_url"]
    head_repo_url = pull_request["head"]["repo"]["git_url"]
    user = pull_request['base']['repo']['owner']['login']
    repo = pull_request['base']['repo']['name']

    log.debug("Received GitHub pull request notification for "
              "%s %s, (%s) from: %s",
              base_repo_url, number, action, head_repo_url)

    if action not in ("opened", "synchronize"):
        log.info("Ignored '%s' action." % action)
        return Response(status=204)
    gh = get_client(app.config, user, repo)
    try:
        lintrc = get_lintrc(gh)
    except:
        log.warn('Cannot download .lintrc file, skipping checks')
    log.error(lintrc)

