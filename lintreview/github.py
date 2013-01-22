from flask import url_for
from pygithub3 import Github
import base64
import logging

log = logging.getLogger(__name__)


def get_client(config, user, repo):
    """
    Factory for the Github client
    """
    gh = Github(
        base_url=config['GITHUB_URL'],
        login=config['GITHUB_USER'],
        password=config['GITHUB_PASSWORD'],
        user=user,
        repo=repo)
    return gh


def get_lintrc(gh):
    """
    Download the .lintrc from a repo
    Since pygithub3 doesn't support this,
    some hackery will ensue.
    """
    repo = gh.repos
    parts = ['repos', repo.get_user(), repo.get_repo(), 'contents', '.lintrc']
    path = '/'.join(parts)
    response = repo._client.get(path)
    return base64.b64decode(response.json['content'])


def register_hook(app, user, repo):
    """
    Register a new hook with a user's repository.
    """
    logging.info('Registering hooks for %s/%s' % (user, repo))
    with app.app_context():
        gh = get_client(app.config, user, repo)
        endpoint = url_for('start_review', _external=True)
    hooks = gh.repos.hooks.list().all()
    found = False
    for hook in hooks:
        if hook.name != 'web':
            continue
        if hook.config['url'] == endpoint:
            found = True
            break

    if found:
        msg = "Found existing hook. "\
            "No additional hooks registered."
        log.warn(msg)
        return

    hook = {
        'name': 'web',
        'active': True,
        'config': {
            'url': endpoint,
            'content_type': 'json',
        },
        'events': ['pull_request']
    }
    try:
        gh.repos.hooks.create(hook, user=user, repo=repo)
    except:
        message = "Unable to save webhook. You need to have administration"\
            "privileges over the repository to add webhooks."
        log.error(message)
    logging.warn('Registered hook successfully')
