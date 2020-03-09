from __future__ import absolute_import
import argparse
import lintreview.github as github
import sys

from flask import url_for
from lintreview.web import app
from lintreview.cli.parsers import (
    add_register_command,
    add_unregister_command,
    add_org_register_command
)

def main():
    parser = create_parser()
    args = parser.parse_args()
    args.func(args)


def remove_org_hook(args):
    try:
        process_org_hook(github.unregister_org_hook, args)
        sys.stdout.write('Org hook removed successfully\n')
    except Exception as e:
        sys.stderr.write('Org hook removal failed\n')
        sys.stderr.write(e.message + '\n')
        sys.exit(2)


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
    add_unregister_command(commands)
    add_org_register_command(commands)

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
