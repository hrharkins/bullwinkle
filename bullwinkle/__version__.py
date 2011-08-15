'''
__version__ file for bullwinkle.

Contains the version information attributes that are imported by the
packages of this library.  If run with python -m, prints the version
information in SHELL loadable foramt.
'''

from __changelog__ import CHANGELOG

LICENSE = 'LGPL-3.0'
AUTHOR = 'Rich Harkins'
AUTHOR_EMAIL = 'rich.harkins@gmail.com'
VERSION = CHANGELOG[-1]
PROJECT = 'bullwinkle'
LICENSE_INFO = 'Run python -m bullwinkle.LICENSE for license text'
CHANGELOG_INFO = 'Run python -m bullwinkle.__changelog__ for full log'

__author__ = AUTHOR
__author_email__ = AUTHOR_EMAIL
__version__ = VERSION
__all__ = ['LICENSE', 'LICENSE_INFO',
           'AUTHOR', 'AUTHOR_EMAIL',
           'VERSION', 'PROJECT', '__version__',
           'CHANGELOG', 'CHANGELOG_INFO',
           '__author__', '__author_email__']

if __name__ == '__main__':
    shvar = PROJECT.replace('-', '_').replace(' ', '_').lower()
    print('')
    print('# %r version information (*SH-compatible format)' % PROJECT)
    print('%s_AUTHOR="%s <%s>"' % (shvar, AUTHOR, AUTHOR_EMAIL))
    print('%s_VERSION=%r' % (shvar, VERSION))
    print('%s_LICENSE=%r' % (shvar, LICENSE))
    print('')
    print('# ' + LICENSE_INFO)
    print('# ' + CHANGELOG_INFO)
    print('')

