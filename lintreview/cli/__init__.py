from __future__ import absolute_import
import argparse

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
