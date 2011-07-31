'''
setup -- Setup script for bullwinkle
'''

from bullwinkle.__version__ import *
from setuptools import setup

setup(
    name = 'bullwinkle',
    version = VERSION,
    author = AUTHOR,
    authro_email = AUTHOR_EMAIL,
    description = 'Python tools inspired by Perl::Moose',
    licesne = LICENSE,
    keywords = 'Moose OOP super',
    url = 'http://code.google.com/bullwinkle',
    packages = ['bullwinkle'],
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ]
)

