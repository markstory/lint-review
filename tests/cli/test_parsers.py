from unittest import TestCase
from mock import Mock, call

from tests import conditionally_return
from lintreview.cli.parsers import add_register_command
from lintreview.cli.handlers import register_hook

class TestCliParsers(TestCase):

    def test_add_register_command_adds_register_hook_invocation(self):
        commands = Mock()
        register_command_parser = Mock()

        desc = (
            "Register webhooks for a given user & repo\n"
            "The installed webhook will be used to trigger lint\n"
            "reviews as pull requests are opened/updated.\n"
        )

        commands.add_parser = conditionally_return(register_command_parser, 'register', help=desc)

        expected_add_argument_calls = [
            call(
                '-u',
                '--user',
                dest='login_user',
                help="The OAuth token of the user that has admin rights to the repo "
                    "you are adding hooks to. Useful when the user "
                    "in settings is not the administrator of "
                    "your repositories."
            ),
            call(
                'user',
                help="The user or organization the repo is under."
            ),
            call(
                'repo',
                help="The repository to install a hook into."
            )
        ]

        expected_set_defaults_calls = [
            call(func=register_hook)
        ]

        add_register_command(commands)

        register_command_parser.add_argument.assert_has_calls(expected_add_argument_calls)
        register_command_parser.set_defaults.assert_has_calls(expected_set_defaults_calls)