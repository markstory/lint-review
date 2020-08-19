from lintreview.diff import parse_diff, Diff
from lintreview.fixers.commit_strategy import CommitStrategy
from lintreview.fixers.error import ConfigurationError
import lintreview.docker as docker
import lintreview.git as git
import logging
import re

log = logging.getLogger(__name__)


workflow_strategies = {
    'commit': CommitStrategy
}


def create_context(review_config, repo_path,
                   head_repository, pull_request):
    """Create the context used for running fixers"""
    context = {
        'strategy': review_config.fixer_workflow(),
        'enabled': review_config.fixers_enabled(),
        'author_name': review_config['GITHUB_AUTHOR_NAME'],
        'author_email': review_config['GITHUB_AUTHOR_EMAIL'],
        'repo_path': repo_path,
        'pull_request': pull_request,
        'repository': head_repository,
    }
    return context


def should_run(fixer_context):
    """Check whether or not fixers should run.

    We don't run fixers when the head commit is from
    the bot user. Doing so can cause autofix commits
    to incrementally update the entire file.
    """
    commit = git.show(fixer_context['repo_path'])
    pattern = r'Author:\s*{}'.format(fixer_context['author_name'])
    if re.search(pattern, commit):
        return False
    return True


def run_fixers(tools, base_path, files):
    """Run fixer mode of each tool on each file
    Return a DiffCollection based on the parsed diff
    from the fixer changes.

    If no diff is generated an empty list will be returned"""
    log.info('Running fixers on %d files', len(files))

    docker_files = [docker.apply_base(f) for f in files]
    for tool in tools:
        if tool.has_fixer():
            tool.execute_fixer(docker_files)
    diff = git.diff(base_path, files)
    if diff:
        return parse_diff(diff)
    return []


def find_intersecting_diffs(original, fixed):
    intersection = []
    if not original or not fixed:
        return intersection

    for name in fixed.get_files():
        original_diff = original.all_changes(name)
        if not len(original_diff):
            log.debug('No matching original diff for %s', name)
            continue
        fixed_diff = fixed.all_changes(name)[0]
        hunks = fixed_diff.intersection(original_diff[0])
        if len(hunks):
            intersection.append(Diff(None, name, '00000', hunks=hunks))
    return intersection


def apply_fixer_diff(original_diffs, fixer_diff, strategy_context):
    """Apply the relevant changes from fixer_diff

    Using the original_diff and fixer_diff, find the intersecting
    changes and delegate to the requested workflow strategy
    to apply and commit the changes.
    """
    if 'strategy' not in strategy_context:
        raise ConfigurationError('Missing `workflow` configuration.')

    strategy = strategy_context['strategy']
    if strategy not in workflow_strategies:
        raise ConfigurationError(u'Unknown workflow `{}`'.format(strategy))

    try:
        log.info('Using %s workflow to apply fixer changes', strategy)
        workflow = workflow_strategies[strategy](strategy_context)
    except Exception as e:
        msg = u'Could not create {} workflow. Got {}'.format(strategy, e)
        raise ConfigurationError(msg)

    changes_to_apply = find_intersecting_diffs(original_diffs, fixer_diff)
    if len(changes_to_apply) == 0:
        log.info('No intersecting changes found. Skipping fixer workflow.')
        return
    workflow.execute(changes_to_apply)


def add_strategy(name, implementation):
    """Add a workflow strategy
    Used by different hosting environments to add new workflows
    """
    log.info('Adding %s fixer strategy', name)
    workflow_strategies[name] = implementation


def rollback_changes(path, old_head):
    git.reset_hard(path)
    git.checkout(path, old_head)
