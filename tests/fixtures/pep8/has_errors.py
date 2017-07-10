# Create unused imports
from __future__ import print_function
import os, re

def thing(self):
    thing_two('arg1',
     'arg2')
    print('derp')

def thing_two(arg1, arg2):
    result=arg1*arg2
    if result != arg1:
        print('derp')
