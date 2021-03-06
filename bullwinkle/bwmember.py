'''
bwmember -- Easy to build type-safe propreties

=====================
=== Type checking ===
=====================

Python's approach to object creation works very well for the most part.
However, sometimes one wants to build a class that does type checking on
one or more of its members.  In these cases, member objects come into play:

>>> class Point(BWObject):
...     x = member(int)
...     y = member(int)
...     __bwformat__ = '<%(x)d, %(y)d>'
...     __positional__ = ('x', 'y')
...

Now we can define a point using keyword arguments:

>>> p = Point(5, 7)
>>> p
Point(x=5, y=7)
>>> print p
<5, 7>

Note how the __repr__ came for free and the __str__ was simple to set up.
In addition, we cannot set the values to something invalid:

>>> p.x = 'Hello'
Traceback (most recent call last):
    ...
TypeError: x ('Hello') must be one of: (<type 'int'>)

Now if multiple types are allowed, then they can all be specified as peers.
Each entry can be one of:

 * A python type, in which case the value must be an instance
 * A callable, in which case the value and member object are provided as
    arguments.  The callable returns true if acceptable.
 * A value, in which case if equal to the object is acceptable (None
    works well here).

>>> class Car(BWObject):
...     color = member('BLUE', 'RED', 'BLACK', None)
...     tires = member(int, lambda v, s: v == 'FOUR', default=4)
...
>>> Car(color='BLUE')
Car(color='BLUE', tires=4)
>>> Car(color='BLACK', tires='FOUR')
Car(color='BLACK', tires='FOUR')
>>> Car(color='WHITE')
Traceback (most recent call last):
    ...
TypeError: color ('WHITE') must be one of: ('BLUE', 'RED', 'BLACK', None)

=======================
=== Type conversion ===
=======================

The convert() function indicates that a given type can be converted into
from other types.  For example, let's revisit the Point class:

>>> class NewPoint(BWObject):
...     x = member(into(float, int))
...     y = member(into(float, int))
...
>>> NewPoint(x=1.5, y=1.5)
NewPoint(x=1.5, y=1.5)
>>> NewPoint(x=1, y=2)
NewPoint(x=1.0, y=2.0)

Now Point will accept int or float but won't try to convert unless it
receives an int (but not a string).  If only one positional argument is
provided to into(), then any type will be converted using the converter
function.  Conversion will not occur if the object is already of the type
specified.

Type conversion can also be attempted for all object types:

>>> def namer(o):
...     return 'Denizen<%s>' % o
...
>>> class Denizen(BWObject):
...     name = member(str, into(namer))
...
>>> Denizen(name=4)
Denizen(name='Denizen<4>')

======================
=== Default values ===
======================

When not provided otherwise, the default attribute of the member (set by
the member constructor) will determine what to do (in this order):

 * If the default memebr is a subclass of Exception it will be called with
    the offending name.

 * If the default member is a type, it is called with no arguments.

 * If the default member is a callable, it will be called with the "self"
    object, the member object, and the name.

 * Otherwise, the default object is used as the default value.

In addition, a builder method name may be specified during member
construction.  If provided, the builder is a name of a method on the object
that will accept the default, possibly use it, and return a built value as
appropriate.

>>> import hashlib
>>> class DBConnection(BWObject):
...     dbname = member(str)
...     username = member(str, default=lambda o, n: o.dbname)
...     password = member(str, default='nobody', builder='makepw')
...     cursors = member(list, default=list)
...     host = member(str, builder='get_host')
...
...     def makepw(self, pw):
...         return hashlib.sha1(pw).digest()
...
>>> conn = DBConnection(dbname='testdb')
>>> conn.dbname
'testdb'
>>> conn.username
'testdb'
>>> conn.cursors
[]
>>> print conn.password
6^\xc1zg_2s\xbc\x16\xc7Ga\xad\x83\xf2\xcf\x07\xc5\x9a
>>> conn.host
Traceback (most recent call last):
    ...
TypeError: 'DBConnection' has no builder method 'get_host'

=========================
=== Read-Only Members ===
=========================

Members created using ro=True will reject changes after the initial
creation of the object or via lazy loading using default/builder.

>>> class StringJoiner(BWObject):
...     inputs = member(list, tuple)
...     separator = member(str, default=', ')
...     contents = member(str, builder='combine', ro=True)
...     __bwformat__ = '%(contents)s'
...
...     def combine(self, defvalue):
...         return self.separator.join(self.inputs)
...
>>> joiner = StringJoiner(inputs=('Hello', 'world'), separator=' ')
>>> print joiner
Hello world
>>> joiner.contents = 'blah'
Traceback (most recent call last):
    ...
AttributeError: can\'t set attribute

========================
=== Optional members ===
========================

Members that are not required during definition can be specified with
optional=True.  These memebers will not be checked for value during
object __init__ in BWObject.  Objects with default or builder values will
be set to optional by default.  Setting optional to False will cause the
value to be determined on object init instead of first member use.  Members
are not optional by default otherwise.

IMPORTANT: Optional members that do not have default/builder settings can
            still generate exceptions when probed.  Generally, default
            and/or builder should be used in lieu of optional=True.

>>> p = Point()
Traceback (most recent call last):
    ...
TypeError: 'x', 'y' needs to be specified when constructing 'Point'.

>>> class Circle(Point):
...     radius = member(int, optional=True)
...
>>> c = Circle(1, 2)
>>> c.radius
Traceback (most recent call last):
    ...
AttributeError: radius

====================================
=== Extending superclass members ===
====================================

Members can be extended from the superclass by using the extend() function.
This will integrate the superclass's concept of a member to match a
subclass's conecpt allowing for semi-anonymous modifications of members.
An additional utility function, extend_str allows for manipulation of base
class strings.

>>> class Circle(Point):
...     x = extend(default=0)
...     y = extend(default=0)
...     radius = member(int)
...     __bwformat__ = extend_str(chopright=1,
...                               prefix='C', suffix=' r%(radius)s>')
...
>>> c = Circle(5, y=1, radius=5)
>>> c
Circle(radius=5, x=5, y=1)
>>> print c
C<5, 1 r5>
'''

from __version__ import *
from bwobject import BWObject
from bwmethod import after_super
from bwcached import cached, cachedmethod
import sys

class BWMemberProperty(property):
    pass

NOT_FOUND = type(None)

class BWMember(BWObject):
    ro = False
    default = AttributeError
    builder = None
    optional = False
    extend = False

    def __init__(self, *isa, **_kw):
        self.isa = isa
        self._kw = _kw
        self.init(**_kw)

    def init(self, ro=None, default=NOT_FOUND,
                   optional=None, builder=None):
        if ro is not None:
            self.ro = ro
        if default is not NOT_FOUND:
            self.default = default
        if builder is not None:
            self.builder = builder
        if optional is not None:
            self.optional = optional
        elif default is not NOT_FOUND or builder:
            self.optional = True

    def __bindclass__(self, cls, name):
        p = BWMemberProperty(self.get_reader(cls, name),
                             self.get_writer(cls, name),
                             self.get_deleter(cls, name))
        p.__initobj__ = self.__initobj__
        p.__name__ = name
        p.__member__ = self
        cls.__addmember__(name)
        if not self.optional:
            cls.__require__(name)
        return p

    @cachedmethod
    def checkset(self):
        return self.build_checker(*self.isa)

    def build_checker(self, *isa):
        src = ['def checker(_s, _n, _v):']
        lv = dict(NOT_FOUND=NOT_FOUND)
        def op(src, lv, indent):
            src.append(indent + 'return True')
        self.build_checker_src(isa, op, src, lv)
        src = '\n'.join(src)
        #print >>sys.stderr, src
        #print >>sys.stderr, lv
        try:
            exec src in lv
        except:         # Debug
            print >>sys.stderr, "Source:"
            print >>sys.stderr, src
            raise
        checker = lv.pop('checker')
        checker.__src__ = src
        checker.__isa__ = isa
        return checker

    def build_checker_src(self, isa, op, src, lv, indent='    '):
        for check in isa:
            if check is None:
                src.append(indent + 'if _v is None:')
                op(src, lv, indent + '    ')
            elif isinstance(check, type):
                name = check.__name__
                lv[name] = check
                src.append(indent + 'if isinstance(_v, %s):' % name)
                op(src, lv, indent + '    ')
            elif callable(check):
                name = 'cb_%d' % len(lv)
                lv[name] = check
                if hasattr(check, '__converter__'):
                    allowed = getattr(check, '__from__', ())
                    def fn_op(src, lv, indent):
                        src.append(indent + 'try:')
                        src.append(indent + '    _nv = %s(_s, _n, _v)' % name)
                        src.append(indent + '    if _nv is not NOT_FOUND:')
                        src.append(indent + '        return (_nv,)')
                        src.append(indent + 'except TypeError:')
                        src.append(indent + '    pass')
                        src.append(indent + 'except ValueError:')
                        src.append(indent + '    pass')
                    tc = getattr(check, '__type__', None)
                    if tc is not None:
                        tname = tc.__name__
                        lv[tname] = tc
                        src.append(indent +
                                   'if isinstance(_v, %s):' % tname)
                        src.append(indent + '    return True')
                    if allowed:
                        self.build_checker_src(allowed, fn_op, src, lv, indent)
                    else:
                        fn_op(src, lv, indent)
                else:
                    src.append(indent + 'if %s(_v, _s):' % name)
                    op(src, lv, indent + '    ')
            else:
                name = 'v_%d' % len(lv)
                lv[name] = check
                src.append(indent + 'if %s == _v:' % name)
                op(src, lv, indent + '    ')
        return src, lv

    def __initobj__(self, obj, name, value, NOT_FOUND=NOT_FOUND):
        ovalue = value
        res = self.checkset(name, value)
        while type(res) is tuple:
            value = res[0]
            res = self.checkset(name, value)
        if res:
            obj.__dict__[name,] = value
        else:
            raise TypeError('%s (%s) must be one of: (%s)'
                            % (name,
                               '%r => %r' % (ovalue, value)
                                    if value is not ovalue
                                    else repr(ovalue),
                               ', '.join(map(repr, self.isa))))

    def get_reader(self, cls, name, NOT_FOUND=NOT_FOUND):
        def reader(o):
            obj = o.__dict__.get((name,), NOT_FOUND)
            if obj is NOT_FOUND:
                default = self.default
                if isinstance(default, type):
                    if issubclass(default, Exception):
                        obj = default
                    else:
                        obj = default()
                elif callable(default):
                    obj = default(o, name)
                else:
                    obj = default
                builder = self.builder
                if builder:
                    fn = getattr(o, builder, None)
                    if fn is None:
                        raise TypeError('%r has no builder method %r' %
                                        (type(o).__name__, builder))
                    else:
                        obj = fn(default)
                if isinstance(obj, type) and issubclass(obj, Exception):
                    raise obj(name)
                self.__initobj__(o, name, obj)
            return obj
        return reader

    def get_writer(self, cls, name):
        if self.ro:
            return None
        else:
            return lambda o, v: self.__initobj__(o, name, v)

    def get_deleter(self, cls, name):
        '''
        >>> class MyObject(BWObject):
        ...     x = member(int)
        ...
        >>> obj = MyObject(x=5)
        >>> obj.x
        5
        >>> del obj.x
        >>> obj.x
        Traceback (most recent call last):
            ...
        AttributeError: x
        >>> del obj.x
        Traceback (most recent call last):
            ...
        AttributeError: x
        '''
        if self.ro:
            return None
        else:
            # XXX: Should we just default to no-op instead when not found?
            # I would personally prefer to make "del x.y" an error-free op.
            def deleter(o, name=name, NOT_FOUND=NOT_FOUND):
                if o.__dict__.pop((name,), NOT_FOUND) is NOT_FOUND:
                    raise AttributeError(name)
            return deleter

class Extender(BWObject):
    '''
    Base class for extension members.  The base class is a no-op but
    subclasses can overload extend() to do more complicated tasks:

    >>> class HelloBase(BWObject):
    ...     hello = 'world'
    ...
    >>> class NoOperationSubclass(HelloBase):
    ...     hello = Extender()
    ...
    >>> class QuoteExtender(Extender):
    ...     def extend(self, cls, name, sv):
    ...         return repr(str(sv))
    ...
    >>> class QuoteSubclass(HelloBase):
    ...     hello = QuoteExtender()
    ...
    >>> print NoOperationSubclass().hello
    world
    >>> print QuoteSubclass().hello
    'world'

    An extrended attribute must exist in the base class.

    >>> class NotFound(HelloBase):
    ...     world = Extender()
    ...
    Traceback (most recent call last):
        ...
    TypeError: Cannot extend 'world': not in base classes of 'NotFound'
    '''

    def __init__(_self, *_args, **_kw):
        _self._args = _args
        _self._kw = _kw

    def __bindclass__(self, cls, name):
        super_value = NOT_FOUND
        for base in cls.__mro__[1:]:
            super_value = base.__dict__.get(name, NOT_FOUND)
            if super_value is not NOT_FOUND:
                break
        if super_value is NOT_FOUND:
            raise TypeError('Cannot extend %r: not in base classes of %r'
                            % (name, cls.__name__))
        return self.extend(cls, name, super_value, *self._args, **self._kw)

    def extend(self, cls, name, sv):
        return sv

class StringExtender(Extender):
    '''
    Manipulates base class string members.  This has a shortcut
    "extend_str".

    >>> class HelloBase(BWObject):
    ...     hello = 'world'
    ...
    >>> class Extended(HelloBase):
    ...     hello = extend_str(chopleft=1, chopright=1,
    ...                        prefix='<', suffix='>')
    ...
    >>> class Extended2(HelloBase):
    ...     hello = extend_str(prefix='<', suffix='>')
    ...
    >>> print Extended().hello
    <orl>
    >>> print Extended2().hello
    <world>
    '''

    def extend(self, cls, name, sv, chopleft=0, chopright=None,
                                    prefix='', suffix=''):
        if chopright:
            chopright = -chopright
        else:
            chopright = None
        return prefix + str(sv)[chopleft:chopright] + suffix

class MemberExtender(Extender):
    '''
    Modifies the arguments provided to a base class member declaration.
    This makes it possible to semi-anonymously modify base class memebr
    definitions without having to redefine the entire member specification.
    The "extend" shortcut references this class.

    When constructing the ISA specificaiton, '*' can be used to determine
    where the base class ISA should go.  Omitting all ISA items will
    default to including all base class ISA.

    >>> class MyBase(BWObject):
    ...     test = member(int, default=0)
    ...
    >>> class Subclass(MyBase):
    ...     test = extend('*', float, optional=False, default=NOT_FOUND)
    ...
    >>> print MyBase().test
    0
    >>> print Subclass().test
    Traceback (most recent call last):
        ...
    TypeError: 'test' needs to be specified when constructing 'Subclass'.
    '''

    def extend(self, cls, name, sv, *_args, **_kw):
        isa = _args or '*'
        checks = []
        for item in isa:
            if item == '*':
                checks.extend(sv.__member__.isa)
            else:
                checks.append(item)
        kw = dict(sv.__member__._kw, **_kw)
        kw.pop('extend', None)
        return type(sv.__member__)(*checks, **kw).__bindclass__(cls, name)

def member(*_args, **_kw):
    return BWMember(*_args, **_kw)

def extend(*_args, **_kw):
    return MemberExtender(*_args, **_kw)

def extend_str(*_args, **_kw):
    return StringExtender(*_args, **_kw)

def into(_converter, *_isa):
    def converter(_s, _n, _v):
        return _converter(_v)
    name = '<converter'
    converter.__converter__ = True
    if isinstance(_converter, type):
        name += ' to %r' % _converter
        converter.__type__ = _converter
    else:
        name += ' fn %r' % _converter
    if _isa:
        converter.__from__ = _isa
        name += ' from %r' % _isa
    converter.__name__ = name + '>'
    return converter

