import argparse
import lintreview.github as github

from lintreview.web import app


def main():
    parser = create_parser()
    args = parser.parse_args()
    args.func(args)


def register_hook(args):
    credentials = None
    if args.login_user and args.login_pass:
        credentials = {
            'GITHUB_USER': args.login_user,
            'GITHUB_PASSWORD': args.login_pass
        }
    github.register_hook(app, args.user, args.repo, credentials)


def remove_hook(args):
    print 'unregister'
    print args


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
        help="The user that has admin rights to the repo you "
             "are removing hooks from. Useful when the "
             "user in settings is not the administrator of "
             "your repositories.")
    remove.add_argument(
        '-p',
        '--password',
        dest='login_pass',
        help="The password of the admin user.")
    remove.add_argument('user',
                        help="The user or organization the repo is under.")
    remove.add_argument('repo',
                        help="The repository to remove a hook from.")
    remove.set_defaults(func=remove_hook)

    return parser

if __name__ == '__main__':
    main()
