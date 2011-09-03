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
    blocker = False
    visible = True
    flag = ''

    def __new__(cls, src, *changes):
        if src is None or isinstance(src, Version):
            return src
        elif isinstance(src, basestring):
            return cls(src.split('.'), *changes)
        elif isinstance(src, (int, float)):
            return cls(str(src), *changes)
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

    def details(self, indent=''):
        return '%s%s%s\n%s    * %s' % (
                indent, 
                self,
                ' (%s)' % self.flag if self.flag else '',
                indent,
                '<No log provided>' if self.label is None
                    else self.label if len(self.changes) == 1
                    else ('\n%s    * ' % indent).join(map(str, self.changes)))


class WIPVersion(Version):
    '''
    Flag subclass to indicate versions that are Work-In-Progress and thus
    makiung the changelog unreleasable.

    >>> log = ChangeLog(
    ...     WIPVersion(0,2, 'In progress'),
    ...     Version(0,1, 'Something'),
    ...     )
    >>> log.blocked
    True
    >>> log = ChangeLog(
    ...     Version(0,2, 'Done'),
    ...     Version(0,1, 'Something'),
    ...     )
    >>> log.blocked
    False
    '''
    blocker = True
    flag = 'WIP'

class PlannedVersion(Version):
    '''
    Represents a version not being worked on but having planned features.
    These versions will not appear in the changelog but will not hold up a
    release.

    >>> log = ChangeLog(
    ...     PlannedVersion(0.3, 'TBD'),
    ...     WIPVersion(0.2, 'In progress'),
    ...     Version(0.1, 'Something'),
    ...     )
    >>> log.blocked
    True
    >>> log = ChangeLog(
    ...     PlannedVersion(0.3, 'TBD'),
    ...     Version(0.2, 'Done'),
    ...     Version(0.1, 'Something'),
    ...     )
    >>> log.blocked
    False
    '''
    visible = False
    flag = 'Planned'

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

    Changelogs are not blocked by default:
    >>> ChangeLog().blocked
    False
    '''

    def __new__(cls, *items):
        return super(ChangeLog, cls).__new__(cls, sorted(items))

    def __str__(self):
        return '\n\n'.join(version.details('')
                           for version in reversed(sorted(self))
                           if version.visible)

    @property
    def all(self):
        return '\n\n'.join(version.details('')
                           for version in reversed(sorted(self)))

    __repr__ = __str__

    @property
    def blocked(self):
        for version in self:
            if version.blocker:
                return True
        return False

