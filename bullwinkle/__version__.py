'''
__version__ file for bullwinkle.

Contains the version information attributes that are imported by the
packages of this library.  If run with python -m, prints the version
information in SHELL loadable foramt.
'''

__LICENSE__ = 'LGPL-3.0 (Run python -m bullwinkle.__license__ for text)'
__AUTHOR__ = 'Rich Harkins'
__AUTHOR_EMAIL__ = 'rich.harkins@gmail.com'
__VERSION__ = 1.0
__PROJECT__ = 'bullwinkle'

if __name__ == '__main__':
    print('Project=%r' % __PROJECT__)
    print('Author="%s<%s>"' % (__AUTHOR__, __AUTHOR_EMAIL__))
    print('Version=%r' % __VERSION__)
    print('License=%r' % __LICENSE__)

