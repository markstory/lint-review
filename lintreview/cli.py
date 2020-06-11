import argparse
import lintreview.github as github
import sys

from flask import url_for
from lintreview.web import app


def main():
    parser = create_parser()
    args = parser.parse_args()
    args.func(args)


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
    credentials = None
    if args.login_user:
        credentials = {
            'GITHUB_OAUTH_TOKEN': args.login_user,
        }

    with app.app_context():
        if credentials:
            credentials['GITHUB_URL'] = app.config['GITHUB_URL']
            repo = github.get_repository(
                credentials,
                args.user,
                args.repo)
        else:
            repo = github.get_repository(
                app.config,
                args.user,
                args.repo)
        endpoint = url_for('start_review', _external=True)
    func(repo, endpoint)


def create_parser():
    desc = """
    Command line utilities for lintreview.
    """
    parser = argparse.ArgumentParser(description=desc)

    commands = parser.add_subparsers(
        title="Subcommands",
        description="Valid subcommands")

    desc = """
    Register webhooks for a given user & repo
    The installed webhook will be used to trigger lint
    reviews as pull requests are opened/updated.
    """
    register = commands.add_parser('register', help=desc)
    register.add_argument(
        '-u',
        '--user',
        dest='login_user',
        help="The user that has admin rights to the repo "
             "you are adding hooks to. Useful when the user "
             "in settings is not the administrator of "
             "your repositories.")
    register.add_argument(
        '-p',
        '--password',
        dest='login_pass',
        help="The password of the admin user.")
    register.add_argument('user',
                          help="The user or organization the repo is under.")
    register.add_argument('repo',
                          help="The repository to install a hook into.")
    register.set_defaults(func=register_hook)

    desc = """
    Unregister webhooks for a given user & repo.
    """
    remove = commands.add_parser('unregister', help=desc)
    remove.add_argument(
        '-u', '--user',
        dest='login_user',
        help="The OAuth token of the user that has admin rights to the repo "
             "you are removing hooks from. Useful when the "
             "user in settings is not the administrator of "
             "your repositories.")
    remove.add_argument('user',
                        help="The user or organization the repo is under.")
    remove.add_argument('repo',
                        help="The repository to remove a hook from.")
    remove.set_defaults(func=remove_hook)

    return parser


if __name__ == '__main__':
    main()
