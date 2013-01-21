from flask import url_for
from pygithub3 import Github
import logging


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
    hooks = gh.repos.hooks.list(user, repo)
    found = False
    for hook in hooks:
        if hook['name'] != 'web':
            continue
        if hook['config']['url'] == endpoint:
            found = True
            break

    if found:
        logging.info('Found existing hook')
        return

    hook = {
        'name': 'web',
        'config': {
            'url': endpoint,
            'content_type': 'json',
        },
        'events': ['pull_request']
    }
    result = gh.repos.hooks.create(hook, user, repo)
    if result.ok:
        logging.info('Registered hook successfully')
    else:
        logging.error('Hook registration failed')
