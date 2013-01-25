
NULL = type(None)

def wrapper(wrap_fn=None, auto_name=True, auto_doc=True):
    '''
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
    ...     # Do something complex with stuff...
    ...     return stuff
    >>> always_span('hello')
    '<span>hello</span>'

    The same wrapper can then be used for other purposes too:

    >>> d = dict(hello='world')
    >>> spanner = tagger(d.get, 'span')
    >>> spanner('hello')
    '<span>world</span>'
    '''

    if wrap_fn is None:
        return lambda f: wrapper(f, auto_name=auto_name,
                                    auto_doc=auto_doc)
    else:
        def builder(_fn=None, *_args, **_kw):
            if not _fn:
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

