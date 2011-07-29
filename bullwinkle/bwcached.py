'''
bwcached -- Lazy loading properties

Provides simple ways to produce lazy loaded values.  These are slimmer than
the assocaited lazy member() functions of bwmember and work for many cases.
In addition, these do NOT require BWObject to work so may be preffed in
some applications.
'''

def cached(fn):
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
            target.__dict__[name] = obj
            return obj
    cls = type(fn.__name__,
               (object,),
               dict(__doc__=fn.__doc__, __get__=wrapper))
    return cls()

def classcached(fn):
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
        setattr(target, name, obj)
        return obj
    cls = type(fn.__name__,
               (object,),
               dict(__doc__=fn.__doc__, __get__=wrapper))
    return cls()

