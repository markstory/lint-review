#!/usr/bin/env python

# Register webhooks for a github repository
#
# Uses the settings and configuration defined
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('user', help="The user or organization the repo is under.")
    parser.add_argument('repo', help="The repository to install a hook into.")
    args = parser.parse_args()


if __name__ == '__main__':
    main()
