import logging
import github3
import github3.checks
import requests
from requests.packages.urllib3.util.retry import Retry

log = logging.getLogger(__name__)

GITHUB_BASE_URL = 'https://api.github.com/'

CHECKSUITE_HEADER = github3.checks.CheckSuite.CUSTOM_HEADERS


def get_client(config):
    """
    Factory for the Github client
    """
    if 'GITHUB_OAUTH_TOKEN' not in config:
        raise KeyError('Missing GITHUB_OAUTH_TOKEN in application config. '
                       'Update your settings.py file.')

    session = get_session(config.get('GITHUB_CLIENT_RETRY_OPTIONS', None))

    if config.get('GITHUB_URL', GITHUB_BASE_URL) != GITHUB_BASE_URL:
        client = github3.GitHubEnterprise(
            config['GITHUB_URL'],
            token=config['GITHUB_OAUTH_TOKEN'],
            session=session)
    else:
        client = github3.GitHub(
            token=config['GITHUB_OAUTH_TOKEN'],
            session=session)
    return client


def get_session(retry_options=None):
    if retry_options is None or not isinstance(retry_options, dict):
        retry_options = {}
    session = github3.session.GitHubSession()
    retry_adapter = requests.adapters.HTTPAdapter(
        max_retries=Retry(**retry_options))
    session.mount('http://', retry_adapter)
    session.mount('https://', retry_adapter)
    return session


def get_repository(config, user, repo):
    gh = get_client(config)
    return gh.repository(owner=user, repository=repo)


def get_lintrc(repo, ref):
    """
    Download the .lintrc from a repo
    """
    log.info('Fetching lintrc file')
    response = repo.file_contents('.lintrc', ref)
    return response.decoded.decode('utf-8')


def register_hook(repo, hook_url):
    """
    Register a new hook with a user's repository.
    """
    log.info('Registering webhook for %s on %s', hook_url, repo.full_name)
    hooks = repo.hooks()
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
        repo.create_hook(**hook)
    except:
        message = ("Unable to save webhook. You need to have administration"
                   "privileges over the repository to add webhooks.")
        log.error(message)
        raise
    log.info('Registered hook successfully')


def unregister_hook(repo, hook_url):
    """
    Remove a registered webhook.
    """
    log.info('Removing webhook for %s on %s', hook_url, repo.full_name)
    hooks = repo.hooks()
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
        repo.hook(hook_id).delete()
    except:
        message = ("Unable to remove webhook. You will need admin "
                   "privileges over the repository to remove webhooks.")
        log.error(message)
        raise
    log.info('Removed hook successfully')
