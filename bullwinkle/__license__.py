'''
__license__ -- bullwinkle license module

Loads and dumps the included LICENSE file if used via python -m or simply
exports the entire file as a LICENSE module attribute.
'''

from __version__ import *
import os

LICENSE = open(os.path.join(os.path.dirname(__file__), 'LICENSE')).read()

if __name__ == '__main__':
    print LICENSE

