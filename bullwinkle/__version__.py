'''
__version__ file for bullwinkle.

Contains the version information attributes that are imported by the
packages of this library.  If run with python -m, prints the version
information in SHELL loadable foramt.
'''

class Version(tuple):
    def __new__(cls, src):
        if src is None or isinstance(src, Version):
            return src
        elif isinstance(src, basestring):
            return Version(src.split('.'))
        elif isinstance(src, (int, float)):
            return Version(str(src))
        else:
            return super(Version, cls).__new__(cls, src)

    def __add__(self, other):
        if isinstance(other, basestring):
            return str(self) + other
        else:
            return super(Version, self).__add__(other)

    def __radd__(self, other):
        if isinstance(other, basestring):
            return other + str(self)
        else:
            return other.__add__(self)

    def __str__(self):
        return '.'.join(self)

    def __repr__(self):
        return 'Version(%r)' % str(self)

LICENSE = 'LGPL-3.0 (Run python -m bullwinkle.__license__ for text)'
AUTHOR = 'Rich Harkins'
AUTHOR_EMAIL = 'rich.harkins@gmail.com'
VERSION = Version('0.2.4')
PROJECT = 'bullwinkle'

if __name__ == '__main__':
    print('Project=%r' % PROJECT)
    print('Author="%s<%s>"' % (AUTHOR, AUTHOR_EMAIL))
    print('Version=%r' % VERSION)
    print('License=%r' % LICENSE)

