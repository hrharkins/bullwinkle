'''
bwcached -- Lazy loading properties

Provides simple ways to produce lazy loaded values.  These are slimmer than
the assocaited lazy member() functions of bwmember and work for many cases.
In addition, these do NOT require BWObject to work so may be preffed in
some applications.

To create a property that generates the output on first access apply
@cached to the method:

>>> class Factorial(object):
...     def __init__(self, n):
...         self.n = n
...
...     @cached
...     def value(self):
...         if self.n < 2:
...             return 1
...         else:
...             return self.n * self.next_fact.value
...
...     @cached
...     def next_fact(self):
...         return Factorial(self.n - 1)
...
>>> f = Factorial(10)
>>> f.value
3628800

========================
=== Volatile results ===
========================

Sometimes it is necessary to return a value that should not be cached.  In
these cases, simply return a cached.volatile() result:

>>> class DictLookup(object):
...     'Track a dictionary, only cache if it exists.'
...     def __init__(self, src, key, default=None):
...         self.src = src
...         self.key = key
...         self.default = default
...
...     @cached
...     def value(self):
...         'Get the value, cache if it exists'
...         print "Getting value"
...         obj = self.src.get(self.key, KeyError)
...         if obj is KeyError:
...             return cached.volatile(self.default)
...         else:
...             return obj
...
>>> d = {}
>>> dl = DictLookup(d, 'var', 'NOPE')
>>> dl.value
Getting value
'NOPE'
>>> d['var'] = 'hello world'
>>> dl.value
Getting value
'hello world'
>>> dl.value
'hello world'

=========================================
=== Accessing the underlying function ===
=========================================

In some rare cases it is helpful to access the underlying method (to access
__doc__, etc).  For @cached, simply access it through the class:

>>> DictLookup.value.__doc__
'Get the value, cache if it exists'
'''

from __version__ import *
import types, sys

class Volatile(object):
    __slots__ = ['obj']

    def __init__(self, obj):
        self.obj = obj

def cached(fn, Volailte=Volatile):
    '''
    Decorates a method that (normally) should only be called once to
    compute the value of an attribute.  Once called, unless the function
    returns a cached.volatile, the result will be stored as the attribute
    until cleared via del.

    >>> class Joiner(object):
    ...     def __init__(self, src, sep=' '):
    ...         self.src = src
    ...         self.sep = sep
    ...
    ...     @cached
    ...     def value(self):
    ...         print "Computing value"
    ...         result = self.sep.join(self.src)
    ...         if isinstance(self.src, list):
    ...             # Return volatile as list might change...
    ...             return cached.volatile(result)
    ...         else:
    ...             return result
    ...
    ...     def __str__(self):
    ...         return self.value
    ...
    >>> j = Joiner(('Hello', 'world'))
    >>> print j
    Computing value
    Hello world
    >>> print j
    Hello world
    >>> j = Joiner(['Hello', 'world'])
    >>> print j
    Computing value
    Hello world
    >>> print j
    Computing value
    Hello world
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
    Decorates a class method that (normally) should only be called once to
    compute the value of an attribute.  Once called, unless the function
    returns a cached.volatile, the result will be stored as the attribute
    until cleared via del.

    >>> class DocLoader(object):
    ...     @classcached
    ...     def docs(cls):
    ...         print 'Loading docs'
    ...         if isinstance(cls.docsrc, (list, tuple)):
    ...             return classcached.volatile(' '.join(cls.docsrc))
    ...         else:
    ...             return cls.docsrc.read()
    ...

    >>> import StringIO
    >>> class FileDocLoader(DocLoader):
    ...     docsrc = StringIO.StringIO('Hello world')
    ...
    >>> dl = FileDocLoader()
    >>> dl.docs
    Loading docs
    'Hello world'
    >>> dl.docs
    'Hello world'
    >>> dl = FileDocLoader()
    >>> dl.docs
    'Hello world'

    >>> class JoinDocLoader(DocLoader):
    ...     docsrc = ('Hello', 'world')
    ...
    >>> dl = JoinDocLoader()
    >>> dl.docs
    Loading docs
    'Hello world'
    >>> dl.docs
    Loading docs
    'Hello world'
    >>> dl = JoinDocLoader()
    >>> dl.docs
    Loading docs
    'Hello world'
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
    Decorates a function that produces a method dynamically.  This is used
    for closure-based actviities that generate inline functions based on
    parameters.  Results can still be volaitle.

    >>> class BinaryOp(object):
    ...     def __init__(self, fn):
    ...         self.fn = fn
    ...
    ...     @cachedmethod
    ...     def op(self):
    ...         'Passes integer values to fn'
    ...         print "Generating function"
    ...         if self.fn is None:
    ...             return cachedmethod.volatile(self.null_fn)
    ...         else:
    ...             return lambda self, a, b: self.fn(int(a), int(b))
    ...
    ...     def null_fn(self, a, b):
    ...         return 0
    >>> adder = BinaryOp(lambda a, b: a + b)
    >>> adder.op(3, 5)
    Generating function
    8
    >>> adder.op(3, 5)
    8
    >>> BinaryOp.op.__doc__
    'Passes integer values to fn'
    >>> anonfn = BinaryOp(None)
    >>> anonfn.op(3, 5)
    Generating function
    0
    >>> anonfn.op(3, 5)
    Generating function
    0
    >>> anonfn.fn = lambda a, b: a - b
    >>> anonfn.op(3, 5)
    Generating function
    -2
    >>> anonfn.op(3, 5)
    -2
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
cachedmethod.volatile = Volatile

def classcachedmethod(fn, Volailte=Volatile):
    '''
    Similar to @cachedmethod except works for classmethods like @classcached.

    >>> class Value(object):
    ...     def __init__(self, src):
    ...         self.value = self.convert(src)
    ...
    ...     converter_name = None
    ...     @classcachedmethod
    ...     def convert(cls):
    ...         if cls.converter_name is None:
    ...             return classcachedmethod.volatile(lambda c, v: v)
    ...         else:
    ...             return getattr(cls, cls.converter_name)
    ...
    >>> class IntValue(Value):
    ...     converter_name = 'to_int'
    ...     @classmethod
    ...     def to_int(cls, v):
    ...         return int(v)
    ...
    >>> v = Value('Hello')
    >>> v.value
    'Hello'
    >>> iv = IntValue('50')
    >>> iv.value
    50
    '''

    name = fn.__name__
    def wrapper(self, target, cls=None, MethodType=types.MethodType):
        target = cls or type(target)
        obj = fn(target)
        if type(obj) is not Volatile:
            if isinstance(obj, classmethod):
                print >>sys.stderr, 'GETTING', obj
                obj = obj.__get__(cls)
            elif not isinstance(obj, MethodType):
                print >>sys.stderr, 'BINDING', obj
                obj = classmethod(obj).__get__(cls)
            setattr(target, name, obj)
            return obj
        else:
            obj = obj.obj
            if isinstance(obj, classmethod):
                print >>sys.stderr, 'v-GETTING', obj
                obj = obj.__get__(cls)
            elif not isinstance(obj, MethodType):
                print >>sys.stderr, 'v-BINDING', obj
                obj = MethodType(obj, cls, type(cls))
            return obj
    cls = type(fn.__name__,
               (object,),
               dict(__doc__=fn.__doc__, __get__=wrapper))
    return cls()
classcachedmethod.volatile = Volatile

