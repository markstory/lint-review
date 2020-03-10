from __future__ import absolute_import
import sys

from lintreview.cli.parsers import create_parser


def main():
    parse_args(sys.argv[1:])


def parse_args(arg_list):
    parser = create_parser()
    args = parser.parse_args(arg_list)
    args.func(args)


if __name__ == '__main__':
    main()
