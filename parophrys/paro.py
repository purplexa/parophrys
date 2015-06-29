from parophrys import cli
import os
import sys

try:
    sys.path.insert(0, os.getcwd())
    import commands
except ImportError:
    print 'no commands directory'
finally:
    sys.path.pop(0)
