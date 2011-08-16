'''
bwversion -- Manage version numbers and change logs

This module simplifies the process of specifying and comparing version
descriptors and then grouping them into change log objects.  The objects
can then be printed easily.
'''

class Version(tuple):
    '''
    Manages a version number and associated changes.

    >>> Version(0.1)
    0.1
    >>> Version('0.1.2')
    0.1.2
    >>> Version('0.1.2') > Version('0.1')
    True

    Giving Version None or another Version will simply return the passed
    value:

    >>> Version(None)
    >>> v = Version(0.5)
    >>> Version(v) is v
    True

    Versions can be freely converted to strings:

    >>> v = Version(0.5)
    >>> str(v)
    '0.5'
    >>> 'v' + v
    'v0.5'
    >>> v + ' (version)'
    '0.5 (version)'
    >>> Version(0.5) + (1,)
    0.5.1
    >>> (0, 5) + Version(1)
    0.5.1

    Special care must be given to % formatting as Version objects are
    actually tuples:

    >>> 'Version %s' % v
    Traceback (most recent call last):
        ...
    TypeError: not all arguments converted during string formatting
    >>> 'Version %s' % str(v)
    'Version 0.5'
    >>> 'Version %s' % (v,)
    'Version 0.5'
    '''

    def __new__(cls, src, *changes):
        if src is None or isinstance(src, Version):
            return src
        elif isinstance(src, basestring):
            return Version(src.split('.'), *changes)
        elif isinstance(src, (int, float)):
            return Version(str(src), *changes)
        else:
            obj = super(Version, cls).__new__(cls, src)
            obj.changes = changes
            if len(changes) == 0:
                obj.label = None
            elif len(changes) == 1:
                obj.label = changes[0]
            else:
                obj.label = changes
            return obj

    def __add__(self, other):
        if isinstance(other, basestring):
            return str(self) + other
        else:
            return type(self)(super(Version, self).__add__(other))

    def __radd__(self, other):
        if isinstance(other, basestring):
            return other + str(self)
        else:
            return Version(other.__add__(self))

    def __str__(self):
        return '.'.join(map(str, self))
    __repr__ = __str__

class ChangeLog(tuple):
    '''
    >>> ChangeLog(
    ...     Version(0.1, 'Version 0.1'),
    ...     Version(0.2, 'Change A in 0.2', 'Change B in 0.2'),
    ... )
    ...
    0.2
        * Change A in 0.2
        * Change B in 0.2
    <BLANKLINE>
    0.1
        * Version 0.1
    '''

    def __new__(cls, *items):
        return super(ChangeLog, cls).__new__(cls, items)

    def __str__(self):
        return '\n\n'.join(
            '%s\n    * %s' % (
                version,
                '<No log provided>' if version.label is None
                    else version.label if len(version.changes) == 1
                    else '\n    * '.join(map(str, version.changes))
                ) for version in reversed(sorted(self)))

    __repr__ = __str__


