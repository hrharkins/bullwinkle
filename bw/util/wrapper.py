
NULL = type(None)

def wrapper(wrap_fn=None, auto_name=True, auto_doc=True):
    '''Simplifies and unifies the function wrapping operation.

    =======
    Summary
    =======

    Makes wrapping of functions and methods simpler by removing the dance
    required to know whether the wrapper function is called with argments
    or without.  This is not fool-proof if the first argument is a
    function but works iin so many cases it is not generally a problem.

    The original function is returned from the wrapper if the wrapped
    function does not return anything.  Otherwise, if the returned value is
    not NULL, then that value is returned, allowing an override function to
    be produced.  If, however, the intended return is None (which is used
    to return the default normally), then returning NULL (type(None))
    signals a desire to return None instead.

    The _args, and _kw provided are automatically provided to the wrapper
    function when it is invoked, whether immeidately or during function
    compsition.

    =======
    Example
    =======

    Suppose we want a wrapper that surrounds the result of a function in
    some static text:

    >>> @wrapper
    ... def tagger(fn, tagname):
    ...     def tag_wrapper(*_args, **_kw):
    ...         result = fn(*_args, **_kw)
    ...         return '<%s>%s</%s>' % (tagname, result, tagname)
    ...     return tag_wrapper

    We can now use that to wrap HTML tags around function calls:

    >>> @tagger('span')
    ... def always_span(stuff):
    ...     'Does something complex with "stuff"'
    ...     return stuff
    >>> always_span('hello')
    '<span>hello</span>'

    The same wrapper can then be used for other purposes too:

    >>> d = dict(hello='world')
    >>> spanner = tagger(d.get, 'span')
    >>> spanner('hello')
    '<span>world</span>'

    ===================================
    Return Types from Wrapped Functions
    ===================================

    The wrapper function does not need to return anything if it is simply
    modifying the function's attributes for example:

    >>> @wrapper
    ... def mark_function(fn):
    ...     fn.__here__ = True

    >>> @mark_function
    ... def hello(): pass

    >>> hello.__here__
    True

    If the result of wrapping should be to return None, then returning NULL
    (or type(None) is requried:

    >>> d = {}
    >>> @wrapper
    ... def consumer(fn):
    ...     d[fn.__name__] = fn
    ...     return NULL     # Or type(None)

    >>> @consumer
    ... def doubler(x): return x * 2

    >>> doubler is None
    True
    >>> d['doubler'](2)
    4

    Note also that @wrapper takes care of the nuances of zero-arguments
    versus omitted argument cases:

    >>> @consumer()
    ... def tripler(x): return x * 3

    >>> d['tripler'](2)
    6

    ===================================
    Wrapped Function Name and Docstring
    ===================================

    Note that the name of the wrapped function (always_scan) was left
    untouched as well as the doc string:

    >>> always_span.__name__
    'always_span'
    >>> always_span.__doc__
    'Does something complex with "stuff"'

    In some rare cases this is not desired and the resulting object should
    be propagated without modifications of those sorts.  This is necessary
    for things that can't (or don't want) __name__ and/or __doc__ set such
    as types:

    >>> @wrapper(auto_name=False, auto_doc=False)
    ... def const_stringer(fn):
    ...     class Stringer(object):
    ...         __str__ = fn
    ...     return type(fn.__name__, (Stringer,), {})

    >>> @const_stringer
    ... def hello(o): return 'world'

    >>> hello.__name__
    'hello'
    >>> print hello()
    world
    '''

    if wrap_fn is None:
        return lambda f: wrapper(f, auto_name=auto_name,
                                    auto_doc=auto_doc)
    else:
        def builder(_fn=None, *_args, **_kw):
            if _fn is None:
                return lambda f: builder(f, **_kw)
            elif not callable(_fn):
                return lambda f: builder(f, _fn, *_args, **_kw)
            else:
                result = wrap_fn(_fn, *_args, **_kw)
                if result is None:
                    return _fn
                elif result is type(None):
                    return None
                else:
                    if auto_name:
                        result.__name__ = _fn.__name__
                    if auto_doc:
                        result.__doc__ = _fn.__doc__
                    return result
        builder.__name__ = wrap_fn.__name__
        builder.__doc__ = wrap_fn.__doc__
        builder.__dict__.update(wrap_fn.__dict__)
        return builder

@wrapper(auto_name=False, auto_doc=False)
def cached(fn, name=None):
    '''Keep results from method calls.

    =======
    Summary
    =======

    Produces a special type of property that will keep the result of
    method calls in the contining object's dict for later to avoid
    re-calculation.  Only on the first access will the method be called.

    =======
    Example
    =======

    Suppose we have a simple Vector class that depends on tuple so that
    each object is strictly read-only:

    >>> class Vector(tuple):
    ...     pass

    Now suppose we want to calculate magnitude on the Vector.  We could:

    >>> class Vector(tuple):
    ...     calculated = 0
    ...
    ...     @property
    ...     def magnitude(self):
    ...         # Return the square root of the sum of squares
    ...         self.calculated += 1
    ...         return sum(n ** 2 for n in self) ** 0.5

    Now, every time we want the magnitude from a Vector it would be
    re-calculated:

    >>> v = Vector((3, 4))
    >>> v.magnitude
    5.0
    >>> v.magnitude
    5.0
    >>> v.magnitude
    5.0
    >>> v.magnitude
    5.0
    >>> v.magnitude
    5.0
    >>> v.calculated
    5

    @cached allows for a drop-in replacement for lazy evaluation of
    attributes:

    >>> class Vector(tuple):
    ...     calculated = 0
    ...
    ...     @cached
    ...     def magnitude(self):
    ...         # Return the square root of the sum of squares
    ...         self.calculated += 1
    ...         return sum(n ** 2 for n in self) ** 0.5

    >>> v = Vector((3, 4))
    >>> v.magnitude
    5.0
    >>> v.magnitude
    5.0
    >>> v.magnitude
    5.0
    >>> v.magnitude
    5.0
    >>> v.magnitude
    5.0

    Now, how many times did that get calculated?

    >>> v.calculated
    1

    A clear improvement if the inputs are constant.

    ===============
    Volatile Values
    ===============

    If the value produced by a cached method should NOT be cached then
    either the result can be wrapped in a Volatile object or raised in a
    Volatile object:

    >>> class Loader(object):
    ...     data = None
    ...     called = 0
    ...
    ...     @cached
    ...     def load(self):
    ...         self.called += 1
    ...         if self.data is None:
    ...             return Volatile(self.data)
    ...         else:
    ...             return self.data

    >>> l = Loader()
    >>> l.load is None
    True
    >>> l.load is None
    True
    >>> l.load is None
    True
    >>> l.load is None
    True
    >>> l.load is None
    True
    >>> l.called
    5

    >>> l.data = 'Hello'
    >>> l.load
    'Hello'
    >>> l.load
    'Hello'
    >>> l.load
    'Hello'
    >>> l.load
    'Hello'
    >>> l.load
    'Hello'
    >>> l.called
    6

    For deep calls, Volatile can be raised as an exception too:

    >>> class Loader(object):
    ...     data = None
    ...     called = 0
    ...
    ...     @cached
    ...     def load(self):
    ...         self.called += 1
    ...         return self.probe()
    ...
    ...     def probe(self):
    ...         if self.data is None:
    ...             raise Volatile(self.data)
    ...         else:
    ...             return self.data

    >>> l = Loader()
    >>> l.load is None
    True
    >>> l.load is None
    True
    >>> l.load is None
    True
    >>> l.load is None
    True
    >>> l.load is None
    True
    >>> l.called
    5

    >>> l.data = 'Hello'
    >>> l.load
    'Hello'
    >>> l.load
    'Hello'
    >>> l.load
    'Hello'
    >>> l.load
    'Hello'
    >>> l.load
    'Hello'
    >>> l.called
    6

    '''

    name = fn.__name__ if name is None else name
    def getter(self, target, cls=None, fn=fn, name=name, Volatile=Volatile):
        try:
            obj = fn(target)
        except Volatile, v:
            return v.o
        else:
            if type(obj) is Volatile:
                return obj.o
            else:
                setattr(target, name, obj)
                return obj
    return type(name, (object,), dict(__get__=getter, __doc__=fn.__doc__))()

class Volatile(Exception):
    __slots__ = ['o']

    def __init__(self, obj):
        self.o = obj
