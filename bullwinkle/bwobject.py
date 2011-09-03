'''
bwobject -- Base class required to use most bullwinkle features

This module exports the BWObject base class that integrates the necessary
metaclass that make most of the other features possible.
'''

from __version__ import *
import sys

class BWObjectMeta(type):
    '''
    Provides the machinery for making Object work.  It scans any derived
    class of Objecct for __bindclass__ and, if found, calls it with the
    class and attribute name as parameters.  If the function returns
    anything but None, that is used to replace the called function.

    See also:
    Object.makemeta()
    '''

    def __init__(cls, typename, typebases, typedict):
        super(BWObjectMeta, cls).__init__(typename, typebases, typedict)
        for name, value in typedict.iteritems():
            fn = getattr(value, '__bindclass__', None)
            if fn is not None:
                replacement = fn(cls, name)
                if replacement is not None:
                    if replacement is type(None):
                        delattr(cls, name)
                    else:
                        setattr(cls, name, replacement)

class BWObject(object):
    '''
    Base class for any object that wants to use bullwinkle extensions to
    object.  These extensions include:

    * Ability to use super_* method decorators to autmatically call
        superclass methods.

    * Ability for member objects to bind to the class automatically
        by providing a __bindclass__ method on the object.

    * Ability to define complex properties by simple declaration.

    The base class __init__ eliminates the need for __init__ in many
    circumstances as well.  All args and kwargs provided are added to
    properties of the type that implement an __initobj__ method.  The
    method is called on construction:

    >>> class CheckingProperty(object):
    ...     def __init__(self, type_check):
    ...         self.type_check = type_check
    ...
    ...     def __initobj__(self, obj, name, value):
    ...         setattr(obj, name, self.type_check(value))
    ...
    >>> class MyObject(BWObject):
    ...     attr = CheckingProperty(int)
    ...
    >>> obj = MyObject(attr=5)
    >>> obj.attr
    5
    >>> obj = MyObject(attr='7')
    >>> obj.attr
    7
    >>> obj = MyObject(attr='Hello')
    Traceback (most recent call last):
        ...
    ValueError: invalid literal for int() with base 10: 'Hello'

    Positional arguments can be listed using a __positional__ attribute on
    the BWObject subclass:

    >>> class Point(BWObject):
    ...     x = CheckingProperty(int)
    ...     y = CheckingProperty(int)
    ...     __positional__ = ('x', 'y')
    ...
    >>> Point(1, 2).x
    1
    >>> Point(1, 2).y
    2
    >>> Point(1, 2, 3)
    Traceback (most recent call last):
        ...
    TypeError: Point() can only accept up to 2 positional arguments.
    >>> Point(1, 2, x=3)
    Traceback (most recent call last):
        ...
    TypeError: Multiple definitions for 'x'

    Keywords that aren't assocaited with __initobj__ properties are given
    to the __initkw__ method:

    >>> class Circle(Point):
    ...     def __initkw__(self, name, value):
    ...         if name == 'radius':
    ...             self.radius = int(value)
    ...             return True
    ...         else:
    ...             super(Circle, self).__initkw__(name, value)
    ...
    >>> c = Circle(1, 2, radius=1)
    >>> c = Circle(1, 2, huh='What')
    Traceback (most recent call last):
        ...
    TypeError: Circle cannot accept keyword huh

    The __bindclass__ methods can do some other important things:

     * Update __bwmembers__ to list all members atuomatically during repr.

     * Update __required__ to list all members that must be initialized
        during construction.

     * Return a different object to replace the member with.  Returning
        type(None) removes the member completely.

    >>> class CheckingProperty(object):
    ...     def __init__(self, type_check, required=True):
    ...         self.type_check = type_check
    ...         self.required = required
    ...
    ...     def __initobj__(self, obj, name, value):
    ...         setattr(obj, name, self.type_check(value))
    ...
    ...     def __bindclass__(self, cls, name):
    ...         if self.type_check is None:
    ...             return type(None)
    ...         cls.__addmember__(name)
    ...         if self.required:
    ...             cls.__require__(name)
    ...
    >>> class Point(BWObject):
    ...     x = CheckingProperty(int)
    ...     y = CheckingProperty(int)
    ...     fake = CheckingProperty(None)
    ...     __positional__ = ('x', 'y')
    ...
    >>> Point(1, 2)
    Point(x=1, y=2)
    >>> Point(1)
    Traceback (most recent call last):
        ...
    TypeError: 'y' needs to be specified when constructing 'Point'.

    Additionally, a __bwformat__ class attribute will define the default
    way that objects are stringified.  All % formatting is done via
    keywords, which are mapped to the object's members.

    >>> class FormattingPoint(Point):
    ...     __bwformat__ = '<%(x)s, %(y)s>'
    ...
    >>> print FormattingPoint(1, 2)
    <1, 2>
    >>> print Point(1, 2)
    Point(x=1, y=2)
    '''

    __metaclass__ = BWObjectMeta
    __positional__ = ()
    __bwformat__ = None

    @classcahced
    def __init__(_cls):
        if self.__bwinit__ is not None:
            return self.__bwinit__
        else:
            return lambda _self: None

    def ___init__(_self, *_args, **_kw):
        positional = _self.__positional__
        if len(_args) > len(positional):
            raise TypeError(
                '%s() can only accept up to %d positional arguments.'
                % (type(_self).__name__, len(positional)))
        elif positional:
            for name, value in zip(positional, _args):
                if name in _kw:
                    raise TypeError('Multiple definitions for %r' % name)
                else:
                    _kw[name] = value
        cls = type(_self)
        for name, value in _kw.iteritems():
            obj = getattr(cls, name, None)
            fn = getattr(obj, '__initobj__', None)
            if fn is not None:
                fn(_self, name, value)
            else:
                _self.__initkw__(name, value)
        required = getattr(_self, '__required__', ())
        if required:
            NOT_FOUND = type(None)
            missing = []
            for name in required:
                if name not in _kw:
                    not_found = getattr(type(_self), name, NOT_FOUND)
                    value = getattr(_self, name, not_found)
                    # XXX: Not sure why coverage is flagging the following
                    # line with the for loop above...
                    if value is not_found: # pragma: no partial
                        missing.append(name)
            if missing:
                raise TypeError('%s needs to be specified when constructing %r.'
                                % (', '.join(map(repr, missing)),
                                    type(_self).__name__))

    @classmethod
    def __addmember__(cls, name):
        members = cls.__dict__.get('__bwmembers__')
        if members is None:
            members = []
            for base in cls.__bases__:
                members.extend(getattr(base, '__bwmembers__', ()))
        cls.__bwmembers__ = (name,) + tuple(m for m in members if m != name)

    @classmethod
    def __require__(cls, name):
        required = cls.__dict__.get('__required__')
        if required is None:
            required = []
            for base in cls.__bases__:
                required.extend(getattr(base, '__required__', ()))
            required = tuple(required)
        required += (name,)
        cls.__required__ = sorted(required)

    def __initkw__(self, name, value):
        raise TypeError('%s cannot accept keyword %s' %
                        (type(self).__name__, name))

    @classmethod
    def mix(cls, *others, **kw):
        '''
        When mixing in Object with other classes, this class method will
        make creating the correct metaclass easier.

        For example, consider if we previously have this class with a
        metaclass:
        >>> class MyClassMeta(type):
        ...     def __init__(cls, *args):
        ...         cls.MyClassMeta = 'HERE'
        >>> class MyClass(object):
        ...     __metaclass__ = MyClassMeta

        Now we want to add Object to the cl;ass hierarchy:
        >>> class MyJoined(MyClass, BWObject):
        ...     pass
        ... #doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        TypeError: Error when calling the metaclass bases
            metaclass conflict: ...

        To fix this, we will create a mix base between Object and other
        classes:
        >>> class MyJoined(BWObject.mix(MyClass, object)):
        ...     pass
        >>> obj = MyJoined()
        >>> obj.MyClassMeta
        'HERE'
        '''

        names = ', '.join(c.__name__ for c in (others + (cls,))),
        basemeta = []
        bases = others + (cls,)
        front = []
        back = []
        for c in bases:
            metaclass = getattr(c, '__metaclass__', None)
            if metaclass is not None:
                basemeta.append(metaclass)
                front.append(c)
            else:
                back.append(c)
        bases = tuple(front + back)
        metabase = type('<metaclass for %s>' % names, tuple(basemeta), {})
        return metabase('<mixin-base for %s>' % names, bases,
            dict(kw, __module__=cls.__module__))

    def __str__(self):
        format = getattr(self, '__bwformat__', None)
        if format:
            return format % self.__objdict__
        else:
            return repr(self)

    @property
    def __objdict__(self):
        class ObjectDict(object):
            def __getitem__(od, name):
                return getattr(self, name)
        return ObjectDict()

    def __repr__(self):
        name = type(self).__name__
        members = sorted(getattr(self, '__bwmembers__', ()))
        kw = ', '.join('%s=%r' % (member, getattr(self, member, None))
                       for member in members)
        return '%s(%s)' % (name, kw)

