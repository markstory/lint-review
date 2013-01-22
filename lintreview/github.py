from flask import url_for
from pygithub3 import Github
import logging

log = logging.getLogger(__name__)


def register_hook(app, user, repo):
    """
    Register a new hook with a user's repository.
    """
    logging.info('Registering hooks for %s/%s' % (user, repo))
    with app.app_context():
        endpoint = url_for('start_review', _external=True)
        gh = Github(
            base_url=app.config['GITHUB_URL'],
            login=app.config['GITHUB_USER'],
            password=app.config['GITHUB_PASSWORD'])
    hooks = gh.repos.hooks.list(user=user, repo=repo).all()
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
