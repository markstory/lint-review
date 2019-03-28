"""
Sample Python File with PEP8 Errors.

Used for testing the pep8.Tool
"""
# Create unused imports
import os, re

def thing(self):
    """Do a thing that has errors."""
    thing_two('arg1',
     'arg2')
    print('derp')

def thing_two(arg1, arg2):
    """Do a second thing that also has errors."""
    result=arg1*arg2
    if result <> arg1:
        print('derp')
