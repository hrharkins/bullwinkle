'''
bwmethods -- Bullwinkle method construction kit.

Provides functions for the construction of methods at compile time.  Many
of these are meant for overriding base class methods and manipulating their
results.  This draws etensively from Perl::Moose but adds some Python
flavour to make things fit in a Pythonic world.
'''

from bwobject import BWObject
from __version__ import *

class MethodBuilder(BWObject):
    require_base = True
    want_args = True
    want_result = False
    can_override = False

    def __new__(cls, fn=None, **_kw):
        if fn is None:
            return lambda f: cls(f, **_kw)
        else:
            return super(MethodBuilder, cls).__new__(cls)

    def __init__(self, fn, **_kw):
        self.fn = fn
        self.init(**_kw)

    def init(self, require_base=None, want_args=None,
                   can_override=None, want_result=None):
        if require_base is not None:
            self.require_base = require_base
        if want_args is not None:
            self.want_args = want_args
        if want_result is not None:
            self.want_result = want_result
        if can_override is not None:
            self.can_override = can_override

    def __bindclass__(self, cls, name):
        method = self.build_wrapper(cls, name)
        method.__name__ = name
        method.__doc__ = self.fn.__doc__
        return method

    def build_wrapper(self, cls, name):
        code = ['def wrapper(_self, *_args, **_kw):']
        self.encode_wrapper(code)
        v = self.get_wrapper_dict(cls, name)
        src = '\n'.join(code)
        exec src in v
        wrapper = v.pop('wrapper')
        wrapper.__src__ = src
        return wrapper

    def get_wrapper_dict(self, cls, name):
        d = dict(cls=cls, name=name, fn=self.fn)
        if self.can_override:
            d['type_none'] = type(None)
        return d

    def encode_wrapper(self, code):
        raise NotImplementedError('No encode defined for %r' % self)

class SuperMethodBuilder(MethodBuilder):
    '''
    Base class for all super-class overriding methods.
    '''

    def __bindclass__(self, cls, name):
        if self.require_base:
            if getattr(super(cls, cls), name, None) is None:
                raise TypeError('Method %r is required in superclasses of %r' %
                    (name, cls.__name__))
        return super(SuperMethodBuilder, self).__bindclass__(cls, name)

    def encode_get_base_result(self, code):
        if self.require_base:
            code.append(
                '    res = getattr(super(cls, _self), name)(*_args, **_kw)',
            )
        else:
            code.extend((
                '    super_fn = getattr(super(cls, _self), name, None)',
                '    if super_fn is None:',
                '        res = None',
                '    else:',
                '        res = super_fn(*_args, **_kw)'
            ))

    def encode_do_fn(self, code):
        if self.can_override:
            code.append('    override = ' + self.get_fn_call())
        else:
            code.append('    ' + self.get_fn_call())

    def get_fn_call(self):
        args = ('_self',) + self.get_fn_positional_args()
        if self.want_args:
            args += ('*_args',)
        args += self.get_fn_keyword_args()
        if self.want_args:
            args += ('**_kw',)
        return 'fn(%s)' % ', '.join(args)

    def get_fn_positional_args(self):
        if self.want_result:
            return ('res',)
        else:
            return ()

    def get_fn_keyword_args(self):
        return ()

    def encode_override(self, code):
        if self.can_override:
            code.extend((
                '    if override is type_none:',
                '        return None',
                '    elif override is not None:',
                '        return override',
            ))

    def encode_return(self, code):
        code.append('    return res')

class OverrideSuperMethodBuild(SuperMethodBuilder):
    '''
    >>> class Sub(BWObject):
    ...     @override_super
    ...     def fn(self):
    ...         return 'Hello'
    ...
    Traceback (most recent call last):
        ...
    TypeError: Method 'fn' is required in superclasses of 'Sub'
    >>> class Base(BWObject):
    ...     def fn(self):
    ...         return 'Hello'
    ...
    >>> class Sub(Base):
    ...     @override_super
    ...     def fn(self):
    ...         return 'World'
    ...
    >>> b = Base()
    >>> s = Sub()
    >>> b.fn()
    'Hello'
    >>> s.fn()
    'World'
    '''

    def build_wrapper(self, cls, name):
        return self.fn
override_super = OverrideSuperMethodBuild

class BeforeSuperMethodBuilder(SuperMethodBuilder):
    '''
    >>> class Sqrt(BWObject):
    ...     def sqrt(self, arg):
    ...         return arg ** .5
    ...
    >>> class OnlyPositiveSqrt(Sqrt):
    ...     @before_super
    ...     def sqrt(self, arg):
    ...         if (arg < 0):
    ...             return 0
    ...
    >>> s = Sqrt()
    >>> ops = OnlyPositiveSqrt()
    >>> s.sqrt(-1)
    Traceback (most recent call last):
        ...
    ValueError: negative number cannot be raised to a fractional power
    >>> ops.sqrt(-1)
    0
    '''

    can_override = True

    @override_super
    def encode_wrapper(self, code):
        self.encode_do_fn(code)
        self.encode_override(code)
        self.encode_get_base_result(code)
        self.encode_return(code)
before_super = BeforeSuperMethodBuilder

class AfterSuperMethodBuilder(SuperMethodBuilder):
    '''
    >>> class Base(BWObject):
    ...     y = None
    ...     def fn(self, x):
    ...         return x * 2
    ...
    >>> class Sub(Base):
    ...     @after_super
    ...     def fn(self, x):
    ...         self.y = x
    ...         return self.y
    ...
    >>> b = Base()
    >>> s = Sub()
    >>> b.fn(5)
    10
    >>> s.fn(5)
    10
    >>> b.y
    >>> s.y
    5
    '''

    @override_super
    def encode_wrapper(self, code):
        self.encode_get_base_result(code)
        self.encode_do_fn(code)
        self.encode_override(code)
        self.encode_return(code)
after_super = AfterSuperMethodBuilder

class FollowSuperMethodBuilder(AfterSuperMethodBuilder):
    '''
    >>> class Base(BWObject):
    ...     def __init__(self, x):
    ...         self.x = x
    ...
    >>> class Sub(Base):
    ...     @follow_super
    ...     def __init__(self):
    ...         self.x *= 2
    ...
    >>> b = Base(5)
    >>> s = Sub(5)
    >>> b.x
    5
    >>> s.x
    10
    '''
    want_args = False
    can_override = False
follow_super = FollowSuperMethodBuilder

class FilterSuperMethodBuilder(AfterSuperMethodBuilder):
    '''
    >>> class Doubler(BWObject):
    ...     def apply(self, arg):
    ...         return arg * 2
    ...
    >>> class Quadrupler(Doubler):
    ...     @filter_super
    ...     def apply(self, res, arg):
    ...         return res * 2
    ...
    >>> d = Doubler()
    >>> q = Quadrupler()
    >>> d.apply(2)
    4
    >>> q.apply(2)
    8
    '''
    want_result = True
    can_override = True
filter_super = FilterSuperMethodBuilder

class AroundSuperMethodBuilder(SuperMethodBuilder):
    '''
    >>> class Base(BWObject):
    ...     def fn(self, x):
    ...         return x ** 2
    ...
    >>> class Sub(Base):
    ...     @around_super
    ...     def fn(self, fn, x):
    ...         x += 1
    ...         res = fn(x * 2)
    ...         return res - 1
    ...
    >>> b = Base()
    >>> s = Sub()
    >>> b.fn(5)
    25
    >>> s.fn(5)
    143
    '''

    want_result = False
    can_override = False

    @override_super
    def encode_wrapper(self, code):
        self.encode_do_fn(code)
        self.encode_return(code)

    @follow_super
    def init(self):
        if self.want_result:
            raise TypeError('Cannot get base result in around methods')
        if self.can_override:
            raise TypeError('Overrides are meaningless in around methods')

    @override_super
    def encode_do_fn(self, code):
        if self.require_base:
            code.append('    super_fn = getattr(super(cls, _self), name)')
        else:
            code.append('    super_fn = getattr(super(cls, _self), name, None)')
        code.append('    res = ' + self.get_fn_call())

    @filter_super(want_args=False)
    def get_fn_positional_args(self, res):
        return res + ('super_fn',)

around_super = AroundSuperMethodBuilder

def override_result(v, type_none=type(None)):
    return type_none if v is None else v

