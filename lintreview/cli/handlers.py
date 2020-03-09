import sys

import lintreview.github as github

def register_hook(args):
    try:
        process_hook(github.register_hook, args)
        sys.stdout.write('Hook registered successfully\n')
    except Exception as e:
        sys.stderr.write('Hook registration failed\n')
        sys.stderr.write(e.message + '\n')
        sys.exit(2)

def remove_hook(args):
    try:
        process_hook(github.unregister_hook, args)
        sys.stdout.write('Hook removed successfully\n')
    except Exception as e:
        sys.stderr.write('Hook removal failed\n')
        sys.stderr.write(e.message + '\n')
        sys.exit(2)

def process_hook(func, args):
    """
    Generic helper for processing hook commands.
    """
    credentials = get_credentials(args)
    repo = github.get_repository(credentials, args.user, args.repo)
    endpoint = get_endpoint()
    func(repo, endpoint)