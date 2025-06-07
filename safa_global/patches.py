import collections
import sys

# Fix for collections.Iterator removed in Python 3.10
if sys.version_info >= (3, 10) and not hasattr(collections, 'Iterator'):
    collections.Iterator = collections.abc.Iterator