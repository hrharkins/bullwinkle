'''
setup -- Setup script for bullwinkle
'''

from bullwinkle.__version__ import *
from setuptools import setup
import sys

if CHANGELOG.blocked:
    print >>sys.stderr, ''
    print >>sys.stderr, 'Blocking versions present in changelog:'
    print >>sys.stderr, ''
    for version in CHANGELOG:
        if version.blocker:
            print >>sys.stderr, version.details()
            print >>sys.stderr, ''
    sys.exit(1)

setup(
    name = 'bullwinkle',
    version = VERSION,
    author = AUTHOR,
    author_email = AUTHOR_EMAIL,
    description = 'Python tools inspired by Perl::Moose',
    licesne = LICENSE,
    keywords = 'Moose OOP super',
    url = 'http://code.google.com/p/bullwinkle',
    packages = ['bullwinkle'],
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ]
)

