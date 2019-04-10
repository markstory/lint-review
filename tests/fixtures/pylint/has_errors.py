# Create unused imports
import os, re

def thing(self):
    return  thing_two('arg1',
     'arg2')


def thing_two(arg1, arg2, arg3):
    """A thinger for thinging but returning nothing
    """
    result=arg1*arg2
    if result == arg1:
        pass
    elif result == '':
        pass
