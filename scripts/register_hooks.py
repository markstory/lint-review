#!/usr/bin/env python

# Register webhooks for a github repository
#
# Uses the settings and configuration defined
from lintreview.web import app
from lintreview.github import register_hook
import argparse


def main():
    desc = """
    Register webhooks for a given user & repo
    The installed webhook will be used to trigger lint
    reviews as pull requests are opened/updated.
    """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('user',
                        help="The user or organization the repo is under.")
    parser.add_argument('repo',
                        help="The repository to install a hook into.")
    args = parser.parse_args()

    register_hook(app, args.user, args.repo)


if __name__ == '__main__':
    main()
