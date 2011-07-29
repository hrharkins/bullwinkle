from __version__ import *

import os

LICENSE = open(os.path.join(os.path.dirname(__file__), 'LICENSE')).read()

if __name__ == '__main__':
    print LICENSE

