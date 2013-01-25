
from wrapper import wrapper, cached, NULL
class NotFoundError(KeyError):
    pass
NOT_FOUND = NotFoundError

class ChainedDict(object):
    '''Dictionary that automatically gets values from other dictionaries.

    =======
    Summary
    =======

    Manages a dictionary that draws from other dictionaries to handle
    values not stored in it.

    =======
    Example
    =======

    Suppose we have two dictionaries that contain different sets of items:

    >>> d1 = dict(x=5, z=9)
    >>> d2 = dict(y=7, z=3)

    Now suppose we want an object that can draw for either one:

    >>> cd = ChainedDict(d1, d2)
    >>> cd['x']
    5
    >>> cd['y']
    7

    =============
    Base Ordering
    =============

    Note that earlier bases override later ones:

    >>> cd['z']
    9

    In addition, these genrerally follow Python's rules for base classes to
    deal with hidden base dictionaries:

    >>> root = ChainedDict(x='root_x')
    >>> sub1 = ChainedDict(root)
    >>> sub2 = ChainedDict(root, x='sub2_x')
    >>> cd = ChainedDict(sub1, sub2)

    So, this tree would look like:

          /-- SUB1 <-\
    CD <-<            |-- ROOT
          \-- SUB2 <-/

    And if this was a depth-first style basing, ROOT's "x" would win since
    a depth-first would search all of SUB1's tree before trying SUB2's.
    Instead:

    >>> cd['x']
    'sub2_x'

    This is because common bases are searched LAST (just like Python
    classes).  Thus, the dictionary resolution order would be:

    CD <-- SUB1 <-- SUB2 <-- ROOT

    ============
    Missing Keys
    ============

    Missing keys work largely as expected:

    >>> cd.get('not_found') is None
    True
    >>> cd['not_found']
    Traceback (most recent call last):
        ...
    KeyError: 'not_found'

    ==============
    Function Bases
    ==============

    Any function can be used as a base to ChainedDict:

    >>> @ChainedDict.function
    ... def doubler(n):
    ...     return n * 2

    >>> cd = ChainedDict(doubler)
    >>> cd[2]
    4

    The dispostion of the default depends on the default= parameter to
    function:

    >>> # Wants the default param
    >>> @ChainedDict.function(default=True)
    ... def wants_default(key, default):
    ...     if key == 'hello':
    ...         return 'world'
    ...     else:
    ...         return None

    >>> cd = ChainedDict(wants_default)
    >>> cd.get('hello')
    'world'
    >>> cd.get('xyz') is None
    True

    >>> # None = use default
    >>> @ChainedDict.function(default=None)
    ... def none_for_default(key):
    ...     return 'world' if key == 'hello' else None

    >>> cd = ChainedDict(none_for_default)
    >>> cd.get('hello')
    'world'
    >>> cd.get('xyz') is None
    True

    >>> # None = valid value
    >>> @ChainedDict.function(default=False)
    ... def none_for_value(key):
    ...     return 'world' if key == 'hello' else None

    >>> cd = ChainedDict(none_for_default)
    >>> cd.get('hello')
    'world'
    >>> cd.get('xyz') is None
    True

    Trying to put something else in for default produces an error:

    >>> @ChainedDict.function(default='hello')
    ... def no_way(): pass
    Traceback (most recent call last):
        ...
    TypeError: default must be True, False, or None, not 'hello'

    Finally, base functions can get the "top" chained dict for furhter
    processing:

    >>> @ChainedDict.function(wants_top=True, default=False)
    ... def adder(cd, k):
    ...     if not k.startswith('_'):
    ...         return cd.get('_' + k, 0) + 1

    >>> cd = ChainedDict(adder, _y=5)
    >>> cd['y']
    6
    '''

    __storage_factory__ = dict

    def __init__(_self, *_bases, **_kw):
        _self.__bases__ = _bases
        _self.__storage__ = _self.__storage_factory__(**_kw)

    def get(self, key, default=None, NOT_FOUND=NOT_FOUND):
        __chaineddict__ = self      # For catching...
        for d, wants_top in self.__dro__:
            if wants_top:
                obj = d(self, key, NOT_FOUND)
            else:
                obj = d(key, NOT_FOUND)
            if obj is not NOT_FOUND:
                return obj
        else:
            return default

    def __getitem__(self, key, NOT_FOUND=NOT_FOUND):
        obj = self.get(key, NOT_FOUND)
        if obj is NOT_FOUND:
            raise KeyError(key)
        else:
            return obj

    @cached
    def __rdro__(self):
        rdro = []
        found = set()
        for base in reversed(self.__bases__):
            if hasattr(base, '__rdro__'):
                for d in base.__rdro__:
                    if id(d) not in found:  # pragma: no branch
                                            # -- says doesn't jump to line
                                            #   above, even with dupe...?
                        found.add(id(d))
                        rdro.append(d)
            else:
                if id(base) not in found:
                    found.add(id(base))
                    if isinstance(base, (dict, ChainedDict)):
                        rdro.append((base.get, False))
                    else:
                        rdro.append((base,
                                    getattr(base, '__wants_top__', False)))
        rdro.append((self.__storage__.get, False))
        return tuple(rdro)

    @cached
    def __dro__(self):
        return tuple(reversed(self.__rdro__))

    @staticmethod
    @wrapper
    def function(fn, default=None, wants_top=False):
        if default is True:
            result = fn
        elif default is None:
            if wants_top:
                def null_handler(t, k, d, fn=fn):
                    o = fn(t, k)
                    if o is None:
                        return d
                    else:
                        return o
            else:
                def null_handler(k, d, fn=fn):
                    o = fn(k)
                    if o is None:
                        return d
                    else:
                        return o
            result = null_handler
        elif default is False:
            if wants_top:
                result = lambda t, k, d, fn=fn: fn(t, k)
            else:
                result = lambda k, d, fn=fn: fn(k)
        else:
            raise TypeError('default must be True, False, or None, not %r'
                            % default)

        result.__wants_top__ = wants_top

        return result

class CachedChainedDict(ChainedDict):
    '''
    Extends ChainedDict by keeping the values it finds in a local cache.
    This is tricky if the underlying dicts could change out from under the
    cache.

    =======
    Example
    =======

    Suppose that we are basing a ChainedDict on something that requires a
    lot of calculations, like this simplified Fibonacci:

    >>> def fib(n):
    ...     return fib(n - 1) + fib(n - 2) if n > 1 else n

    Now this takes a long time as n increases.  Wouldn't it be nice to
    compute this incrementally, keeping the results as we go?  To do so we
    can use a CachedChainedDict and a specialized function:

    >>> @ChainedDict.function(wants_top=True)
    ... def fib(t, n):
    ...     if n >= 2 and int(n) == n:
    ...         return t[n - 1] + t[n - 2]
    ...     elif n == 1:
    ...         return 1
    ...     elif n == 0:
    ...         return 0

    >>> cd = CachedChainedDict(fib)
    >>> cd[5]
    5
    >>> cd[10]
    55
    >>> cd[-1] is None
    Traceback (most recent call last):
        ...
    KeyError: -1

    Just to prove we cached the results:

    >>> sorted(cd.__cache__)
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    '''

    def get(self, key, default=None, NOT_FOUND=NOT_FOUND):
        obj = self.__cache__.get(key, NOT_FOUND)
        if obj is NOT_FOUND:
            obj = super(CachedChainedDict, self).get(key, NOT_FOUND)
            if obj is NOT_FOUND:
                return default
            else:
                self.__cache__[key] = obj
                return obj
        else:
            return obj

    @cached
    def __cache__(self):
        return dict()

