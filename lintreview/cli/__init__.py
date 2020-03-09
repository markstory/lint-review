from __future__ import absolute_import
import argparse
import lintreview.github as github
import sys

from flask import url_for
from lintreview.web import app
from lintreview.cli.parsers import (
    add_register_command,
    add_unregister_command,
    add_org_register_command,
    add_org_unregister_command
)


def main():
    parser = create_parser()
    args = parser.parse_args()
    args.func(args)


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
    add_org_unregister_command(commands)

    return parser


if __name__ == '__main__':
    main()
