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
    '''

    __metaclass__ = BWObjectMeta

    def __init__(_self, **_kw):
        cls = type(_self)
        for name, value in _kw.iteritems():
            obj = getattr(cls, name, None)
            fn = getattr(obj, '__initobj__', None)
            if fn is not None:
                fn(_self, name, value)

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
        >>> class MyJoined(BWObject.mix(MyClass)):
        ...     pass
        >>> obj = MyJoined()
        >>> obj.MyClassMeta
        'HERE'
        '''

        names = ', '.join(c.__name__ for c in (others + (cls,))),
        basemeta = []
        bases = others + (cls,)
        for c in bases:
            metaclass = getattr(c, '__metaclass__', None)
            if metaclass is not None:
                basemeta.append(metaclass)
        metabase = type('<metaclass for %s>' % names, tuple(basemeta), {})
        return metabase('<mixin-base for %s>' % names, bases,
            dict(kw, __module__=cls.__module__))

