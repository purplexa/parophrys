from __future__ import print_function
from parophrys import cli
import os
import sys

try:
    sys.path.insert(0, os.getcwd())
    import commands
except ImportError as e:
    if 'commands' in str(e):
        print('no commands directory')
    else:
        raise
finally:
    sys.path.pop(0)
