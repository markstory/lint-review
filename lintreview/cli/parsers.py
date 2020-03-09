from lintreview.cli.handlers import register_hook

def add_register_command(subcommands_parser):
    desc = (
        "Register webhooks for a given user & repo\n"
        "The installed webhook will be used to trigger lint\n"
        "reviews as pull requests are opened/updated.\n"
    )

    register = subcommands_parser.add_parser('register', help=desc)
    register.add_argument(
        '-u',
        '--user',
        dest='login_user',
        help="The OAuth token of the user that has admin rights to the repo "
             "you are adding hooks to. Useful when the user "
             "in settings is not the administrator of "
             "your repositories.")
    register.add_argument('user',
                          help="The user or organization the repo is under.")
    register.add_argument('repo',
                          help="The repository to install a hook into.")
    register.set_defaults(func=register_hook)