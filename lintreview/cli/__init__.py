from __future__ import absolute_import
import argparse
import lintreview.github as github
import sys

from flask import url_for
from lintreview.web import app
from lintreview.cli.parsers import add_register_command

def main():
    parser = create_parser()
    args = parser.parse_args()
    args.func(args)


def remove_hook(args):
    try:
        process_hook(github.unregister_hook, args)
        sys.stdout.write('Hook removed successfully\n')
    except Exception as e:
        sys.stderr.write('Hook removal failed\n')
        sys.stderr.write(e.message + '\n')
        sys.exit(2)


def register_org_hook(args):
    try:
        process_org_hook(github.register_org_hook, args)
        sys.stdout.write('Org hook registered successfully\n')
    except Exception as e:
        sys.stderr.write('Org hook registration failed\n')
        sys.stderr.write(e.message + '\n')
        sys.exit(2)


def remove_org_hook(args):
    try:
        process_org_hook(github.unregister_org_hook, args)
        sys.stdout.write('Org hook removed successfully\n')
    except Exception as e:
        sys.stderr.write('Org hook removal failed\n')
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


def process_org_hook(func, args):
    """
    Generic helper for processing org hook commands.
    """
    credentials = get_credentials(args)
    org = github.get_organization(credentials, args.org_name)
    endpoint = get_endpoint()
    func(org, endpoint)


def get_credentials(args):
    with app.app_context():
        if args.login_user:
            return {
                'GITHUB_OAUTH_TOKEN': args.login_user,
                'GITHUB_URL': app.config['GITHUB_URL']
            }
        else:
            return app.config


def get_endpoint():
    with app.app_context():
        return url_for('start_review', _external=True)


def create_parser():
    desc = """
    Command line utilities for lintreview.
    """
    parser = argparse.ArgumentParser(description=desc)

    commands = parser.add_subparsers(
        title="Subcommands",
        description="Valid subcommands")

    add_register_command(commands)

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

    desc = """
    Register webhook for a given organization
    The installed webhook will be used to trigger lint
    reviews as pull requests are opened/updated.
    """
    register = commands.add_parser('org-register', help=desc)
    register.add_argument(
        '-u',
        '--user',
        dest='login_user',
        help="The OAuth token of the user that has admin rights to the org "
             "you are adding hooks to. Useful when the user "
             "in settings is not the administrator of "
             "your organization.")
    register.add_argument('org_name',
                          help="The login name of the organization.")
    register.set_defaults(func=register_org_hook)

    desc = """
    Unregister webhooks for a given organization.
    """
    remove = commands.add_parser('org-unregister', help=desc)
    remove.add_argument(
        '-u', '--user',
        dest='login_user',
        help="The OAuth token of the user that has admin rights to the org "
             "you are removing hooks from. Useful when the "
             "user in settings is not the administrator of "
             "your organization.")
    remove.add_argument('org_name',
                        help="The login name of the organization.")
    remove.set_defaults(func=remove_org_hook)

    return parser


if __name__ == '__main__':
    main()
