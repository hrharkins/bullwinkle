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
...

Now we can define a point using keyword arguments:

>>> p = Point(x=5, y=7)
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
...     color = member('BLUE', 'RED', 'BLACK')
...
>>> Car(color='BLUE')
Car(color='BLUE')
>>> Car(color='BLACK')
Car(color='BLACK')
>>> Car(color='WHITE')
Traceback (most recent call last):
    ...
TypeError: color ('WHITE') must be one of: ('BLUE', 'RED', 'BLACK')

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
...     username = member(str, default='nobody')
...     password = member(str, default='nobody', builder='makepw')
...
...     def makepw(self, pw):
...         return hashlib.sha1(pw).digest()
...
>>> conn = DBConnection()
>>> conn.username
'nobody'
>>> print conn.password
6^\xc1zg_2s\xbc\x16\xc7Ga\xad\x83\xf2\xcf\x07\xc5\x9a

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
AttributeError: can't set attribute

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
TypeError: x, y need to be specified when constructing Point.
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

    def __init__(self, *isa, **_kw):
        self.isa = isa
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
        members = cls.__dict__.get('__bwmembers__')
        if members is None:
            members = []
            for base in cls.__bases__:
                members.extend(getattr(base, '__bwmembers__', ()))
            members = tuple(members)
        cls.__bwmembers__ = (p,) + members
        if not self.optional:
            required = cls.__dict__.get('__required__')
            if required is None:
                required = []
                for base in cls.__bases__:
                    required.extend(getattr(base, '__required__', ()))
                required = tuple(required)
            required += (name,)
            cls.__required__ = sorted(required)
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
        exec src in lv
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
                        src.append(indent + 'except:')
                        src.append(indent + '    pass')
                    tc = getattr(check, '__type__', None)
                    if tc is not None:
                        tname = tc.__name__
                        lv[tname] = tc
                        src.append(indent +
                                   'if isinstance(_v, %s):' % tname)
                        src.append(indent + '    return True')
                        src.append(indent + 'else:')
                        sindent = indent + '    '
                    else:
                        sindent = indent
                    if allowed:
                        self.build_checker_src(allowed, fn_op, src, lv, sindent)
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
        res = self.checkset(name, value)
        while type(res) is tuple:
            value = res[0]
            res = self.checkset(name, value)
        if res:
            obj.__dict__[name,] = value
        else:
            raise TypeError('%s (%r) must be one of: (%s)'
                            % (name, value, ', '.join(map(repr, self.isa))))

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
                                        (self, builder))
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
        if self.ro:
            return None
        else:
            # XXX: Should we just default to no-op instead when not found?
            # I would personally prefer to make "del x.y" an error-free op.
            return lambda o: self.__dict__.pop((name,))

def member(*_args, **_kw):
    return BWMember(*_args, **_kw)

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

