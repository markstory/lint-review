from setuptools import setup, find_packages

PACKAGE_NAME = "lintreview"
VERSION = "2.0.0-beta3"

requirements = open('./requirements.txt', 'r')

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description="Lint Review, an automated code review tool that "
                "integrates with github. Integrates with the github API "
                "& a variety of code checking tools.",
    author="Mark Story",
    author_email="mark@mark-story.com",
    packages=find_packages(exclude=['tests*']),
    entry_points={
        'console_scripts': [
            'lintreview = lintreview.cli:main',
        ],
    },
    install_requires=requirements.readlines(),
)
