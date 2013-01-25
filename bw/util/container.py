
from wrapper import cached
NOT_FOUND = KeyError

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

    '''

    __storage_factory__ = dict

    def __init__(_self, *_bases, **_kw):
        _self.__bases__ = _bases
        _self.__storage__ = _self.__storage_factory__(**_kw)

    def get(self, key, default=None, NOT_FOUND=NOT_FOUND):
        for d in self.__dro__:
            obj = d.get(key, NOT_FOUND)
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
                    rdro.append(base)
        rdro.append(self.__storage__)
        return tuple(rdro)

    @cached
    def __dro__(self):
        return tuple(reversed(self.__rdro__))

