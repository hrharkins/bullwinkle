
from bwcached import cachedmethod, classcachedmethod
import sys

class BWCreatable(object):
    @classmethod
    def _new(cls, *_args, **_kw):
        return super(BWCreatable, cls).__new__(cls, *_args, **_kw)

    @classcachedmethod
    def __new__(cls):
        return cls._new

class BWConvertable(BWCreatable):
    '''
    Base class for all operator superclasses.  This provides no default
    operators and cannot convert any objects other than None and itself.

    >>> print BWConvertable(None)
    None
    >>> print BWConvertable(1)
    Traceback (most recent call last):
        ...
    TypeError: Cannot construct BWConvertable from number 1
    >>> print BWConvertable('hello')
    Traceback (most recent call last):
        ...
    TypeError: Cannot construct BWConvertable from string 'hello'
    >>> print BWConvertable([])
    Traceback (most recent call last):
        ...
    TypeError: Cannot construct BWConvertable from sequence []
    >>> print BWConvertable(set())
    Traceback (most recent call last):
        ...
    TypeError: Cannot construct BWConvertable from set set([])
    >>> print BWConvertable({})
    Traceback (most recent call last):
        ...
    TypeError: Cannot construct BWConvertable from dict {}
    >>> class MyType(object):
    ...     pass
    ...
    >>> print BWConvertable(MyType())
    Traceback (most recent call last):
        ...
    TypeError: Cannot construct BWConvertable from <type 'type'>

    >>> class MyConvertable(BWConvertable):
    ...     def __init__(self, x):
    ...         print type(x)
    ...         self.x = x
    ...
    ...     @classmethod
    ...     def from_string(cls, src):
    ...         return cls._new(x=int(src))
    ...
    >>> MyConvertable('5').x
    5
    '''

    def __new__(cls, src):
        if src is None or isinstance(src, cls):
            return src
        elif isinstance(src, basestring):
            return cls.from_string(src)
        elif isinstance(src, (int, float, complex)):
            return cls.from_number(src)
        elif isinstance(src, (tuple, list)):
            return cls.from_sequence(src)
        elif isinstance(src, (frozenset, set)):
            return cls.from_set(src)
        elif isinstance(src, dict):
            return cls.from_dict(src)
        else:
            raise TypeError('Cannot construct %s from %r' %
                            (cls.__name__, src))

    @classmethod
    def from_number(cls, src):
        raise TypeError('Cannot construct %s from number %r' %
                        (cls.__name__, src))

    @classmethod
    def from_string(cls, src):
        raise TypeError('Cannot construct %s from string %r' %
                        (cls.__name__, src))

    @classmethod
    def from_sequence(cls, src):
        raise TypeError('Cannot construct %s from sequence %r' %
                        (cls.__name__, src))

    @classmethod
    def from_set(cls, src):
        raise TypeError('Cannot construct %s from set %r' %
                        (cls.__name__, src))

    @classmethod
    def from_dict(cls, src):
        raise TypeError('Cannot construct %s from dict %r' %
                        (cls.__name__, src))

class BWAdder(BWCreatable):
    def __add__(self, other):
        if not isinstance(other, self):
            other = type(self)(other)
        return type(self)(self.add(self, other))

    def __radd__(self, other):
        if not isinstance(other, self):
            other = type(self)(other)
        return type(self)(self.add(other, self))

    @cachedmethod
    def add(cls, left, right):
        return super(BWAdder, cls).__add__

