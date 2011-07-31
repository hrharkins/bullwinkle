'''
setup -- Setup script for bullwinkle
'''

from __version__ import *
from setuptools import setup

setup(
    name = 'bullwinkle',
    version  =__VERSION,
    author=__AUTHOR__,
    authro_email = __AUTHOR_EMAIL__,
    description = 'Python tools inspired by Perl::Moose',
    licesne = __LICENSE__,
    keywords = 'Moose OOP super',
    url = 'http://code.google.com/bullwinkle',
    packages = ['bullwinkle'],
    long_description = __version__.readme()
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ]
)

