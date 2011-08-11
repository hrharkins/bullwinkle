'''
__version__ file for bullwinkle.

Contains the version information attributes that are imported by the
packages of this library.  If run with python -m, prints the version
information in SHELL loadable foramt.
'''

LICENSE = 'LGPL-3.0 (Run python -m bullwinkle.__license__ for text)'
AUTHOR = 'Rich Harkins'
AUTHOR_EMAIL = 'rich.harkins@gmail.com'
VERSION = 0.2
PROJECT = 'bullwinkle'

if __name__ == '__main__':
    print('Project=%r' % PROJECT)
    print('Author="%s<%s>"' % (AUTHOR, AUTHOR_EMAIL))
    print('Version=%r' % VERSION)
    print('License=%r' % LICENSE)

