#!/usr/bin/env python

# Register webhooks for a github repository
#
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
    parser.add_argument('-u', '--user',
                        dest='login_user',
                        help="The user that has admin rights to the repo you "
                             "are adding hooks to. Useful when the user in "
                             "settings is not the administrator of "
                             "your repositories.")
    parser.add_argument('-p', '--password',
                        dest='login_pass',
                        help="The password of the admin user.")
    parser.add_argument('user',
                        help="The user or organization the repo is under.")
    parser.add_argument('repo',
                        help="The repository to install a hook into.")
    args = parser.parse_args()
    credentials = None
    if args.login_user and args.login_pass:
        credentials = {
            'GITHUB_USER': args.login_user,
            'GITHUB_PASSWORD': args.login_pass
        }
    register_hook(app, args.user, args.repo, credentials)


if __name__ == '__main__':
    main()
