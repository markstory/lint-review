import logging

import github3

log = logging.getLogger(__name__)


def get_client(config):
    """
    Factory for the Github client
    """
    if 'GITHUB_OAUTH_TOKEN' in config:
        gh = github3.login(
            username=config['GITHUB_USER'],
            token=config['GITHUB_OAUTH_TOKEN']
        )
    else:
        gh = github3.login(
            username=config['GITHUB_USER'],
            password=config['GITHUB_PASSWORD']
        )

    return gh


def get_repository(config, user, repo):
    gh = get_client(config)
    return gh.repository(owner=user, repository=repo)


def get_lintrc(gh):
    """
    Download the .lintrc from a repo
    Since pygithub3 doesn't support this,
    some hackery will ensue.
    """
    log.info('Fetching lintrc file')
    response = gh.file_contents('.lintrc')
    return response.decoded


def register_hook(gh, hook_url, user, repo):
    """
    Register a new hook with a user's repository.
    """
    log.info('Registering webhook for %s on %s/%s', hook_url, user, repo)
    hooks = gh.hooks()
    found = False
    for hook in hooks:
        if hook.name != 'web':
            continue
        if hook.config['url'] == hook_url:
            found = True
            break

    if found:
        msg = ("Found existing hook. "
               "No additional hooks registered.")
        log.warn(msg)
        return

    hook = {
        'name': 'web',
        'active': True,
        'config': {
            'url': hook_url,
            'content_type': 'json',
        },
        'events': ['pull_request']
    }
    try:
        gh.create_hook(**hook)
    except:
        message = ("Unable to save webhook. You need to have administration"
                   "privileges over the repository to add webhooks.")
        log.error(message)
        raise
    log.info('Registered hook successfully')


def unregister_hook(gh, hook_url, user, repo):
    """
    Remove a registered webhook.
    """
    log.info('Removing webhook for %s on %s/%s', hook_url, user, repo)
    hooks = gh.hooks()
    hook_id = False
    for hook in hooks:
        if hook.name != 'web':
            continue
        if hook.config['url'] == hook_url:
            hook_id = hook.id
            break

    if not hook_id:
        msg = ("Could not find hook for '%s' "
               "No hooks removed.") % (hook_url)
        log.error(msg)
        raise Exception(msg)
    try:
        gh.hook(hook_id).delete()
    except:
        message = ("Unable to remove webhook. You will need admin "
                   "privileges over the repository to remove webhooks.")
        log.error(message)
        raise
    log.info('Removed hook successfully')
