from setuptools import setup, find_packages
import re

requirements = open('./requirements.txt', 'r')

with open('./lintreview/__init__.py', 'r') as f:
    version = re.search(r"__version__ = '(.*?)'", f.read()).group(1)

setup(
    name='lintreview',
    version=version,
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
