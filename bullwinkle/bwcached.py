'''
bwcached -- Lazy loading properties

Provides simple ways to produce lazy loaded values.  These are slimmer than
the assocaited lazy member() functions of bwmember and work for many cases.
In addition, these do NOT require BWObject to work so may be preffed in
some applications.
'''

from __version__ import *
import types

class Volatile(object):
    __slots__ = ['obj']

    def __init__(self, obj):
        self.obj = obj

def cached(fn, Volailte=Volatile):
    '''
    >>> class MyClass(object):
    ...     def __init__(self, x):
    ...         self.x = x
    ...
    ...     @cached
    ...     def doubled(self):
    ...         print "HERE"
    ...         return self.x * 2
    ...
    >>> c = MyClass(10)
    >>> c.doubled
    HERE
    20
    >>> c.doubled
    20
    >>> c.__dict__['doubled']
    20
    '''

    name = fn.__name__
    def wrapper(self, target, cls=None):
        if target is None:
            return fn
        else:
            obj = fn(target)
            if type(obj) is not Volatile:
                target.__dict__[name] = obj
                return obj
            else:
                return obj.obj
    cls = type(fn.__name__,
               (object,),
               dict(__doc__=fn.__doc__, __get__=wrapper))
    return cls()
cached.volatile = Volatile

def classcached(fn, Volailte=Volatile):
    '''
    >>> class MyClass(object):
    ...     x = 10
    ...
    ...     @classcached
    ...     def doubled(self):
    ...         print "HERE"
    ...         return self.x * 2
    ...
    >>> c = MyClass()
    >>> c.doubled
    HERE
    20
    >>> c.doubled
    20
    >>> MyClass.__dict__['doubled']
    20
    '''

    name = fn.__name__
    def wrapper(self, target, cls=None):
        target = cls or type(target)
        obj = fn(target)
        if type(obj) is not Volatile:
            setattr(target, name, obj)
            return obj
        else:
            return obj.obj
    cls = type(fn.__name__,
               (object,),
               dict(__doc__=fn.__doc__, __get__=wrapper))
    return cls()
classcached.volatile = Volatile

def cachedmethod(fn, Volailte=Volatile):
    '''
    >>> class MyClass(object):
    ...     def __init__(self, x):
    ...         self.x = x
    ...
    ...     @cached
    ...     def doubled(self):
    ...         print "HERE"
    ...         return self.x * 2
    ...
    >>> c = MyClass(10)
    >>> c.doubled
    HERE
    20
    >>> c.doubled
    20
    >>> c.__dict__['doubled']
    20
    '''

    name = fn.__name__
    def wrapper(self, target, cls=None, MethodType=types.MethodType):
        if target is None:
            return fn
        else:
            obj = fn(target)
            if type(obj) is not Volatile:
                obj = MethodType(obj, target, type(target))
                target.__dict__[name] = obj
                return obj
            else:
                return obj.obj
    cls = type(fn.__name__,
               (object,),
               dict(__doc__=fn.__doc__, __get__=wrapper))
    return cls()
cached.volatile = Volatile

def classcachedmethod(fn, Volailte=Volatile):
    '''
    >>> class MyClass(object):
    ...     x = 10
    ...
    ...     @classcached
    ...     def doubled(self):
    ...         print "HERE"
    ...         return self.x * 2
    ...
    >>> c = MyClass()
    >>> c.doubled
    HERE
    20
    >>> c.doubled
    20
    >>> MyClass.__dict__['doubled']
    20
    '''

    name = fn.__name__
    def wrapper(self, target, cls=None):
        target = cls or type(target)
        obj = fn(target)
        if type(obj) is not Volatile:
            obj = classmethod(obj)
            setattr(target, name, obj)
            return obj
        else:
            return obj.obj
    cls = type(fn.__name__,
               (object,),
               dict(__doc__=fn.__doc__, __get__=wrapper))
    return cls()
classcached.volatile = Volatile

