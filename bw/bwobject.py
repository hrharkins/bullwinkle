
from bw.util import NULL, wrapper, CodeBlock, cached
from types import MethodType, FunctionType
FUNC_TYPES = (MethodType, FunctionType)

class BWConstrainable(object):
    def __contains__(self, obj):        # self might be type.
        return obj in self.__bwconstraint__

    def __neg__(self):
        return self.NOT(self)

    def __invert__(self):
        return -self

    def __or__(self, other):
        return self.ANY(self, other)

    def __ror__(self, other):
        return self.ANY(other, self)

    def __and__(self, other):
        return self.ALL(self, other)

    def __rand__(self, other):
        return self.ALL(other, self)

    @classmethod
    def constraint_from_object(cls, obj, FUNC_TYPES=FUNC_TYPES):
        constraint = getattr(obj, '__bwconstraint__', None)
        if constraint is None:
            if isinstance(obj, type):
                return cls.ISA(obj, registry=cls)
            elif isinstance(obj, FUNC_TYPES):
                return cls.OK(obj)
            else:
                return cls.EQ(obj)
        return constraint

    is_factory = constraint_from_object
    # These are defined elsewhere by monkey-pactching.
    ok_factory = None
    isa_factory = None
    does_factory = None
    is_not_factory = None
    any_factory = None
    all_factory = None
    equal_to_factory = None
    not_equal_to_factory = None
    less_than_factory = None
    greater_than_factory = None
    less_than_or_equal_to_factory = None
    greater_than_or_equal_to_factory = None

    @classmethod
    def ISA(cls, *options, **_kw):
        _kw.setdefault('registry', BWObject)
        return cls.isa_factory(*options, **_kw)

    @classmethod
    def DOES(cls, *options, **_kw):
        _kw.setdefault('registry', BWObject)
        return cls.does_factory(*options, **_kw)

    @classmethod
    def OK(_cls, _obj, *_args, **_kw):
        return _cls.ok_factory(_obj, *_args, **_kw)

    @classmethod
    def IS(cls, obj, *_args, **_kw):
        return cls.is_factory(obj, *_args, **_kw)

    @classmethod
    def NOT(cls, obj, **_kw):
        return cls.is_not_factory(cls.is_factory(obj, **_kw))

    @classmethod
    def ANY(cls, *objs, **_kw):
        return cls.any_factory(*objs, **_kw)

    @classmethod
    def ALL(cls, *objs, **_kw):
        return cls.all_factory(*objs, **_kw)

    @classmethod
    def EQ(cls, *objs, **_kw):
        return cls.equal_to_factory(*objs, **_kw)

    @classmethod
    def NE(cls, *objs, **_kw):
        return cls.not_equal_to_factory(*objs, **_kw)

    @classmethod
    def LT(cls, *objs, **_kw):
        return cls.less_than_factory(*objs, **_kw)

    @classmethod
    def GT(cls, *objs, **_kw):
        return cls.greater_than_factory(*objs, **_kw)

    @classmethod
    def LTE(cls, *objs, **_kw):
        return cls.less_than_or_equal_to_factory(*objs, **_kw)

    @classmethod
    def GTE(cls, *objs, **_kw):
        return cls.greater_than_or_equal_to_factory(*objs, **_kw)

    def __repr__(self):     # pragma: doctest no cover
        return '<never>'

IS = BWConstrainable.IS
DOES = BWConstrainable.DOES
OK = BWConstrainable.OK
ISA = BWConstrainable.ISA
NOT = BWConstrainable.NOT
ANY = BWConstrainable.ANY
ALL = BWConstrainable.ALL
EQ = BWConstrainable.EQ
NE = BWConstrainable.NE
LT = BWConstrainable.LT
GT = BWConstrainable.GT
LTE = BWConstrainable.LTE
GTE = BWConstrainable.GTE

class BWMeta(type, BWConstrainable):
    def __init__(cls, typename, typebases, typedict):
        #import sys; print >>sys.stderr, 'BWMeta.__init__', cls
        super(BWMeta, cls).__init__(typename, typebases, typedict)
        for base in reversed(cls.__mro__):
            fn = base.__dict__.get('__bwsetup__')
            #import sys; print >>sys.stderr, '__bwsetup__', base, list(typedict)
            if fn is not None:
                fn(cls, base)

    def ___new__(meta, typename, typebases, typedict):  #pragma: doctest no cover
        # Create a new meta-base for each BWObject type.  This
        # allows us to insert class things via meta_method as well as 
        # make sure we don't have issues with external base classes being
        # mixed with this meta-class (ORM's are common issues otherwise).
        if '__bwmeta__' not in typedict:
            # Compute the base meta-classes of all base classes of the new
            # class.
            metabases = [meta]
            found = set((id(meta),))
            for base in metabases:
                basemeta = type(base)
                if id(basemeta) not in found:
                    found.add(id(basemeta))
                    metabases.append(basemeta)
            #metabases = tuple(type(base) for base in typebases)
            metabases = tuple(metabases)

            # Now create a meta-class to use to create the class.
            clsmeta = type('Meta<%s>' % typename, metabases, dict(typedict))

            import sys; print >>sys.stderr, '1>>>', meta, clsmeta
            # Finally, use that metaclass to do the actual construction.
            return clsmeta(typename, typebases,
                            dict(typedict, __bwmeta__=True))
        else:
            import sys; print >>sys.stderr, '2>>>', meta, list(typedict)
            cls = super(BWMeta, meta).__new__(
                meta, typename, typebases, dict(typedict, __bwmeta__=meta))
            #meta.__init__(cls, typename, typebases, typedict)
            import sys; print >>sys.stderr, cls
            return cls

    def __make_bwinit__(cls, blk):
        for callback in cls.__bwinit_inline__:
            callback(cls, blk)

    def init_inline(cls, fn):
        cls.__bwinit_inline__ += (fn,)
        return fn

    @wrapper(method=True)
    def meta_method(fn, cls):
        setattr(cls, fn.__name__, fn)

    @wrapper(method=True)
    def binder(fn, cls): # pragma: doctest no cover
        'Marks a function as a __bwbind__ function'
        fn.__bwbind__ = True

    @wrapper(method=True)
    def rebinder(fn, cls):
        fn.__bwrebind__ = True

    def __add__(cls, other):
        if isinstance(other, type):
            names = (cls.__dict__.get('__bwadd_parts__', (cls.__name__,)) +
                     other.__dict__.get('__bwadd_parts__', (other.__name__,)))
            name = ' + '.join(names)
            bases = (cls, other)
            typedict = dict(__bwadd_parts__ = names)
        else:
            name = '(' + cls.__name__ + ')<%s>' % ','.join(other)
            bases = (cls,)
            typedict = other
        return type(name, bases, typedict)

    @property
    def __bwconstraint__(cls):
        return cls.__get_bwconstraint__()

    @cached
    def __bwtypes__(cls):
        return {}

    def register(cls, target=None, name=None):
        if target is None and name is None:     # pragma: doctest no cover
            return lambda c: register(c)
        elif isinstance(target, basestring):    # pragma: doctest no cover
            return lambda c: register(c, target)
        else:
            name = name or target.__name__
            registry = cls.__dict__.get('__bwtypes__')
            if registry is None:
                registry = cls.__bwtypes__ = dict()
            registry[name] = target
            return target

    def __getitem__(cls, name):
        for base in cls.__mro__:
            registry = base.__dict__.get('__bwtypes__')
            if registry is not None:
                obj = registry.get(name)
                if obj is not None:
                    return obj
        else:
            raise KeyError('No registered type %r in %r'
                           % (name, cls.__name__))

    def ISA(cls, *options, **_kw):
        _kw.setdefault('registry', cls)
        return cls.isa_factory(*options, **_kw)

# Necessary to deal with Python2/3 compatability
BWObject = BWMeta('BWObject', (object,), dict(
    __doc__ = 
    '''Base for all Bullwinkle-enhanced Python classes.

    =======
    Summary
    =======

    BWObject provides the base or mixin class to enable Bullwinkle features
    on the Python class inheriting from it.  These features include:

    * Ability to modify the class following creation
    * Binding of any or all members to the class via callback
    * Individual metatype creation per class
    * Combinability of classes via the addition operator
    * Creation of type constraints via bitwise-logical operators

    ====================
    Class Initialization
    ====================

    Once a class based on BWObject is created, the __bwsetup__ classmethod
    is invoked upon it.  This method can do many things, though
    registration is a typical use:

    >>> class Registered(BWObject):
    ...     registry = {}
    ...
    ...     def __bwsetup__(cls, base):
    ...         cls.registry[cls.__name__] = cls

    >>> class TypeA(Registered): pass
    >>> class TypeB(Registered): pass
    >>> sorted(Registered.registry)
    ['Registered', 'TypeA', 'TypeB']

    A few things should be noted:

    * The class being initialized will NOT be available by name when
        __bwsetup__ is called.  It is, however, the class passed.

    * All __bwsetup__ methods will be called in base-class-first order.
        This means that a subclass CANNOT prevent a base-class __bwsetup__
        from being executed.

    * As a result, __bwstup__ MUST be a staticmethod that receives cls as
        the first argument instead of a classmethod.

    ================
    Class Arithmetic
    ================

    BWObject subclasses can be added on-the-fly to form new sub-types:

    >>> class Response(BWObject):
    ...     pass

    >>> class NotFound(Response):
    ...     msg = 'not_found'

    >>> class HttpResponse(Response):
    ...     http_status = None

    >>> HttpResponse + NotFound
    <class 'bwobject.HttpResponse + NotFound'>
    >>> (HttpResponse + NotFound).http_status is None
    True

    In addition, dictionaries can be provided via addition to define
    class-level parameters:

    >>> (HttpResponse + NotFound + dict(http_status=500)).http_status
    500

    This sort of mixing-and-matching can be handy for defining class
    interfaces within classes or APIs:

    >>> class Okay(Response):
    ...     msg = 'okay'

    >>> class HttpResponses(object):
    ...     ok = (HttpResponse + Okay + dict(http_status=200))
    ...     not_found = (HttpResponse + NotFound + dict(http_status=404))

    >>> class Request(object):
    ...     responess = None

    >>> class HttpRequest(Request):
    ...     responses = HttpResponses

    >>> def processor(req):
    ...     return req.responses.ok()

    Now processor is unaware of the actual type of request.  It could be
    Http, Ftp, etc., as long as it fulfills the basic "Request" protocol.

    >>> processor(HttpRequest())        # doctest: +ELLIPSIS
    <bwobject.(HttpResponse + Okay)<http_status> object at ...

    ==============
    Member Binding
    ==============

    Upon creation, all BWObject-enhanced classes will scan their members
    (as well as base-class members) for binding methods.  These methods are
    called upon class initialization to potentially enhance the class or
    setup the member in some way.

    To utilize this, the member defines a __bwbind__ attribute on the
    member that is either:

    * A function (or callable) that will be invoked with the class, member
        name, and previous value as positional arguments.

    * Python True meaning the member itself should be called in such a way.

    A typical use for this is for auto-linking a member with the name
    appied by the containing class:

    >>> class DatabaseField(object):        # Note BWObject NOT reqiured
    ...     def __bwbind__(self, cls, name, value):
    ...         cls.columns += (value,)
    ...         self.name = name

    >>> class Table(BWObject):
    ...     columns = ()
    ...     id = DatabaseField()
    ...     data = DatabaseField()

    >>> sorted(column.name for column in Table.columns)
    ['data', 'id']

    If it is important for members to be initialized in a particular order,
    adding an incrementing __bwbindorder__ member tells BWObject what order
    to invoke the bindable methods in:

    >>> class DatabaseField(object):        # Note BWObject NOT reqiured
    ...     sequence = 0
    ...     def __init__(self):
    ...         self.__bwbindorder__ = self.sequence
    ...         type(self).sequence += 1
    ...
    ...     def __bwbind__(self, cls, name, value):
    ...         cls.columns += (value,)
    ...         self.name = name

    >>> class Table(BWObject):
    ...     columns = ()
    ...     id = DatabaseField()
    ...     data = DatabaseField()

    >>> tuple(column.name for column in Table.columns)
    ('id', 'data')

    Bind functions can return one of three things:

    * None -- nothing happens to the member; it is left intact.

    * NULL (type(None)) -- the member is replaced by None

    * Anything else -- the member is replaced by the result

    Being able to replace the member allows for, among other things,
    defining custom getter/setters easily:

    >>> class DatabaseField(object):        # Note BWObject NOT reqiured
    ...     sequence = 0
    ...     def __init__(self, cls):
    ...         self.__bwbindorder__ = self.sequence
    ...         self.check = cls
    ...         type(self).sequence += 1
    ...
    ...     def __bwbind__(self, cls, name, value):
    ...         cls.columns += (value,)
    ...         self.name = name
    ...         attr = '_' + name
    ...         cls = self.check
    ...         return property(lambda s: getattr(s, attr),
    ...                         lambda s, v: setattr(s, attr, cls(v)))

    >>> class Table(BWObject):          # Generalized
    ...     columns = ()
    ...
    ...     def __init__(self, **_kw):
    ...         for name, value in _kw.iteritems():
    ...             setattr(self, name, value)

    >>> class MyTable(Table):
    ...     id = DatabaseField(int)
    ...     data = DatabaseField(str)

    >>> t = MyTable(id='5', data='hello')
    >>> t.id
    5
    >>> t.data
    'hello'
    >>> t = MyTable(id='blah', data='ohno!')
    Traceback (most recent call last):
        ...
    ValueError: invalid literal for int() with base 10: 'blah'

    ======================
    Binding without Values
    ======================

    Rarely, bound members can be used to simply get some sort of configuration
    but be outside the normal class-based hierarchy otherwise.  In these
    cases, returning NULL (type(None)) will replace the member with None
    before proceeding:

    >>> class Configurator(object):
    ...     def __init__(self, **_kw):
    ...         self._kw = _kw
    ...
    ...     def __bwbind__(self, cls, name, value):
    ...         cls._config = dict(cls._config, **self._kw)
    ...         return NULL

    >>> class Configurable(BWObject):
    ...     _config = {}
    ...     my_config = Configurator(hello='world')

    >>> hasattr(Configurable, 'my_config')
    False
    >>> Configurable._config['hello']
    'world'

    ================
    Member Rebinding
    ================

    Binding members can be called on subclasses if the member has
    defined __bwrebind__ and is either a function or "True" (meaning the
    __bwbind__ should be used as the rebinder).  Either way, the function
    operates the same as __bwbind__

    >>> class ClassInserter(object):
    ...     def __bwbind__(self, cls, name, value):
    ...         return [cls.__name__]

    >>> class ClassInserter2(object):
    ...     @BWObject.rebinder
    ...     def __bwbind__(self, cls, name, value):
    ...         if isinstance(value, list):
    ...             value.append(cls.__name__)
    ...         else:
    ...             return [cls.__name__]

    >>> class Base(BWObject):
    ...     x = ClassInserter()
    ...     y = ClassInserter2()

    >>> class Sub(Base):
    ...     pass

    >>> Sub.x
    ['Base']
    >>> Sub.y
    ['Base', 'Sub']

    ''',
    __bwinit_inline__ = (),
    __bwchain__ = lambda _s, *_a, **_kw: super(BWObject, _s).__init__(),
    __get_bwconstraint__ = classmethod(lambda c: BWTypeConstraint(c)),
))

@BWObject.meta_method
def __bwsetup__(cls, base):
    # Scan for local binders first
    callbacks = []
    name_sequences = {}
    for name in cls.__dict__:
        value = cls.__dict__[name]
        if isinstance(value, MethodType): # pragma: doctest no cover
            fn = getattr(value.im_func, '__bwbind__', None)
            sequence = getattr(value.im_func, '__bwbindorder__', 0)
        else:
            fn = getattr(value, '__bwbind__', None)
            sequence = getattr(value, '__bwbindorder__', 0)
        if fn is not None:
            if fn is True:
                fn = value      # pragma: doctest no cover
            callbacks.append((sequence, name, fn))
    callbacks.sort()
    callbacks = cls.__bwcallbacks__ = tuple(callbacks)

    # Exend with binders from base classes that need also be called.
    for base in cls.__mro__:
        for callback in getattr(base, '__bwcallbacks__', ()):
            if callback not in callbacks:
                sequence, name, fn = callback
                rebind = getattr(fn, '__bwrebind__', None)
                if rebind is not None:
                    if rebind is True:
                        rebind = fn
                    callbacks += ((sequence, name, rebind),)

    # Next, apply the callbacks.  These should now be in order of:
    #
    # 1. Proximity to this class
    # 2. Sequence if specified
    # 3. Name of the method
    #
    # While doing this, we'll keep track of the values from higher
    # priority bidings to allow binders that support __bwrebind__ to be
    # called later.
    #
    metainfo = dict()
    for sequence, name, fn in callbacks:
        replacement = fn(cls, name, metainfo.get(name, getattr(cls, name)))
        if replacement is not None:
            metainfo[name] = replacement

    # Finally, update the class with any replacements specified.
    for name, value in metainfo.items():
        if value is NULL:
            delattr(cls, name)
        else:
            setattr(cls, name, value)
BWObject.__bwsetup__

class BWSmartObject(BWObject):
    '''Base for all Bullwinkle-enhanced Python classes.

    =======
    Summary
    =======

    BWSmartObject extends BWObject to provide automatic constructor
    generation.

    ======================
    Constructor Management
    ======================

    Initialization for BWSmartObject instances is slightly different than for
    regular Python instances:

    1. __init__ is called as normal.
    2. BWSmartObject's __init__ calls __bwinit__
    3. __bwinit__ is a method defined on *every* BWSmartObject subclass that
        sets up automated things for the object.
    4. __bwchain__ is called to determine what arguments to send on to base
        classes of the BWSmartObject subclass.

    Any binding member can add code to __bwinit__ by adding an
    init_inline function via @BWSmartObject.init_inline:

    >>> class Field(object):
    ...     sequence = 0
    ...
    ...     def __init__(self, accept, default=NULL):
    ...         self.accept = accept
    ...         self.default = default
    ...         type(self).sequence += 1
    ...         self.__bwbindorder__ = self.sequence
    ...
    ...     def __bwbind__(self, cls, name, value):
    ...         self.name = name
    ...         #import pdb; pdb.set_trace()
    ...         @cls.init_inline
    ...         def setup_member(cls, blk):
    ...             if self.default is not NULL:
    ...                 blk.kwargs[name] = self.default
    ...             else:
    ...                 blk.args.append(name)
    ...             var = blk.anon(self.accept)
    ...             if_blk = blk.add('if not isinstance(%s, %s):', name, var)
    ...             if_blk.add('raise TypeError("%s must be a %s")'
    ...                 % (name, type.__name__))
    ...             blk.add('_self.%s = %s' % (name, name))

    >>> class Table(BWSmartObject):
    ...     id = Field(int, default=0)
    ...     data = Field(str)

    >>> t = Table(data='hello')
    >>> t.id
    0
    >>> t.data
    'hello'

    By constructing a Python function on-the-fly, BWSmartObject initialization
    should perform at most around 3X (or less) slower than a normal Python
    initialization path.  This is a trade-off between convenience and
    speed.  In most cases, this is not too painful, but subclasses are
    always free to define their own __init__ path that avoids BWOject's by
    subclassing BWObject instead, allowing for member binding but
    without the automatic creation of initialization magic.

    '''

    __bwtypes__ = BWObject.__bwtypes__

    def __init__(_self, *_args, **_kw):
        _self.__bwinit__(*_args, **_kw)

    def __bwsetup__(cls, base):
        #import sys; print >>sys.stderr, 'HERE', cls, base
        # Run following BWObject's __bwsetup__

        # And as an added bonus, set up __bwinit__.  This will be converted
        # into a real method on the first use.
        # XXX: Thread safety is an issue here.
        def __bwinit__(_self, *_args, **_kw):
            # Create the method via CodeBlock
            bwinit_blk = CodeBlock()
            bwinit_blk.args = []
            bwinit_blk.kwargs = {}
            cls.__make_bwinit__(bwinit_blk)

            # Make sure we call any base class __init__ as well.
            bwinit_blk.append('_self.__bwchain__(**_kw)')

            # Wrap the block in a function declaration using the args
            # and kw to set things up.
            args = ['_self']
            for arg in bwinit_blk.args:
                args.append(arg)
            for name in bwinit_blk.kwargs:
                value = bwinit_blk.kwargs[name]
                args.append('%s=%s'
                            % (name, bwinit_blk.anon(name, value)))
            args.append('**_kw')
            argstr = ', '.join(args)
            fnblk = CodeBlock('def __bwinit__(%s):' % argstr,
                              bwinit_blk, **bwinit_blk.vars)

            # Now use it.  This wrapper won't be called again for this
            # class.
            #import sys; print >>sys.stderr, fnblk
            bwinit = cls.__bwinit__ = fnblk.extract('__bwinit__')
            bwinit.__source__ = str(fnblk)
            return _self.__bwinit__(*_args, **_kw)
        cls.__bwinit__ = __bwinit__

class BWConstraint(BWObject, BWConstrainable):
    '''Manages the structured checking of variable state.

    =======
    Summary
    =======

    =======
    Example
    =======

    Consider these two BWObject classes:

    >>> class Chocolate(BWObject): pass
    >>> class PeanutButter(BWObject): pass

    To look for one or the other we can simply use the in operator:

    >>> Chocolate() in Chocolate
    True
    >>> Chocolate() in PeanutButter
    False
    >>> PeanutButter() in Chocolate
    False
    >>> PeanutButter() in PeanutButter
    True

    We can also use the "IS" shortcut (or BWConstraint.IS) to accomplish
    the same:

    >>> PeanutButter() in IS(Chocolate)
    False

    To invert, we *could* use Python's not operator, but there are critical
    advantages to using unary - (more details later).  Alternatively, NOT()
    will also work.

    >>> PeanutButter() in -Chocolate
    True
    >>> PeanutButter() in ~Chocolate                    # Also works
    True
    >>> Chocolate() in NOT(PeanutButter)
    True

    To look for any of different options, use bitwise or (|) or ANY():

    >>> PeanutButter() in (Chocolate | PeanutButter)
    True
    >>> Chocolate() in ANY(Chocolate, PeanutButter)
    True

    Finally, the opposite applies to ALL:

    >>> PeanutButter() in (Chocolate & PeanutButter)
    False
    >>> Chocolate() in ALL(Chocolate, PeanutButter)
    False
    >>> (Chocolate + PeanutButter)() in ALL(Chocolate, PeanutButter)
    True

    ==========================
    Generic Python Constraints
    ==========================

    IS/NOT/ANY/ALL is required for handling generic Python types:

    >>> 5 in IS(int)
    True
    >>> 7.5 in ANY(int, float)
    True

    Once a constraint is formed, algebraic operators can take effect:

    >>> 5 in IS(int) | float
    True
    >>> 7 in float | IS(int)
    True

    Additionally, comparisons of value can also be made:

    >>> 'Hello' in ANY('Hello', 'world')
    True
    >>> (5 in EQ(5), 5 in EQ(7))
    (True, False)
    >>> (5 in NE(5), 5 in NE(7))
    (False, True)
    >>> (5 in LT(3), 5 in LT(5), 5 in LT(7))
    (False, False, True)
    >>> (5 in GT(3), 5 in GT(5), 5 in GT(7))
    (True, False, False)
    >>> (5 in LTE(3), 5 in LTE(5), 5 in LTE(7))
    (False, True, True)
    >>> (5 in GTE(3), 5 in GTE(5), 5 in GTE(7))
    (True, True, False)

    These can also be grouped:

    >>> 5 in int & LT(7) & GT(3)
    True

    Constraints can also be based on simple Python functions or bound
    methods:

    >>> 5 in IS(lambda o: o > 3 and o < 7)
    True

    The function can be passed arguments defined at the time of constraint
    construction, but to do so must use the OK (or BWConstrainable.OK)
    wrapper:

    >>> gt = lambda o, v: o > v
    >>> 5 in OK(gt, 3)
    True

    =========================
    Deferred Type Constraints
    =========================

    Because sometimes a type isn't defined at the point of constraint
    definition, BWConstraint permits forward-referencing of registered
    BWObject types by passing the registered name to ISA (not IS):

    >>> c = ISA('Thing')
    >>> @BWObject.register
    ... class Thing(BWObject):
    ...     pass

    >>> Thing() in c
    True

    Registration can be made on regular Python classes as well:

    >>> BWObject.register(int) is int
    True
    >>> 5 in ISA('int')
    True

    And can receive any name desired:

    >>> BWObject.register(int, 'Int') is int
    True
    >>> 5 in ISA('Int')
    True

    Sometimes, registration will happen in other class hierarchies outside
    of BWObject.  To allow for this, use ISA within that BWObject type:

    >>> class MyTypeFamily(BWObject):
    ...     pass

    >>> c = MyTypeFamily.ISA('MyType')

    >>> @MyTypeFamily.register
    ... class MyType(BWObject):
    ...     pass

    >>> MyType() in c
    True

    Type registries can also be accessed via item accesso on the containing
    class family:

    >>> MyTypeFamily['MyType'] is MyType
    True
    >>> MyTypeFamily['UnknownType']
    Traceback (most recent call last):
        ...
    KeyError: "No registered type 'UnknownType' in 'MyTypeFamily'"

    ====================
    Constraint Functions
    ====================

    Although constraints can be checked directly it is sometimes handy to
    conver them to first class Python functions.  This can be done via the
    cached function property:

    >>> fn = ANY(int, str).function
    >>> fn(5)
    True
    >>> fn('Hello')
    True
    >>> fn(5.0)
    False

    ================
    NEVER and ALWAYS
    ================

    Two standard constraint objects exist to handle the none and all cases
    for linking to other elements.

    >>> NEVER, ALWAYS
    (<never>, <always>)
    >>> 5 in NEVER | int
    True
    >>> 5.0 in ALWAYS & float
    True

    These are expected to be used rarely but are included for completeness.

    '''

    def __contains__(self, obj, **_options):
        return self.check(obj, **_options)

    @property
    def __bwconstraint__(self):
        return self

    def check(self, obj, **_options):
        return False

    @cached
    def function(self):
        blk = CodeBlock('def f(v):')
        ok = lambda b, v: b.append('return True')
        self.inline(blk, 'v', ok, None)
        blk.append('return False')
        return blk.result.f

    def inline(self, blk, var, proceed_factory, error_factory, **_options):
        if type(self) is BWConstraint:
            if error_factory:           # pragma: doctest no cover
                blk.add(error_factory(blk, var, 'No value is acceptable'))
        else:
            check_var = blk.anon(self)
            if proceed_factory is not None:
                if_blk = blk.add('if %s in %s:' % (var, check_var))
                proceed_factory(if_blk, var)
                if error_factory:
                    else_blk = blk.add('else:')
                    error_factory(else_blk, var, 'Did not match constraint')
            elif error_factory is not None:         # pragma: doctest no cover
                if_blk = blk.add('if %s not in %s:' % (var, check_var))
                error_factory(if_blk, var, 'Did not match constraint')
NEVER = BWConstraint()

class BWNullConstraint(BWConstraint):
    def check(self, obj, **_options):
        return True

    def inline(self, blk, var,
                     proceed_factory, error_factory,
                     **_options):       # pragma: doctest no cover
        if proceed_factory is not None:
            blk.add(proceed_factory(blk, var))

    def __repr__(self):
        return '<always>'
ALWAYS = BWNullConstraint()

class BWManyConstraint(BWConstraint):
    def __init__(self, *constraints):
        self.constraints = tuple(self.constraint_from_object(constraint)
                                 for constraint in constraints)

class BWAnyConstraint(BWManyConstraint):
    def check(self, obj, **_options):
        for constraint in self.constraints:
            if constraint.check(obj, **_options):
                return True
        else:   # pragma: doctest no cover
            return False

    def inline(self, blk, var, proceed_factory, error_factory, **_options):
        constraint_iter = iter(self.constraints)
        def chainer(blk, var, *_args, **_kw):
            for constraint in constraint_iter:
                return constraint.inline(blk, var, proceed_factory,
                                         chainer, **_options)
            else:
                if error_factory is not None:
                    return error_factory(blk, var, *_args, **_kw)
        return chainer(blk, var, proceed_factory, error_factory, **_options)

    def __repr__(self):     # pragma: doctest no cover
        return '(%s)' % '|'.join(
            '%r' % constraint for constraint in self.constraints)

BWConstrainable.any_factory = BWAnyConstraint

class BWAllConstraint(BWManyConstraint):
    def check(self, obj, **_options):
        for constraint in self.constraints:
            if not constraint.check(obj, **_options):
                return False
        else:
            return True

    def inline(self, blk, var,
                     proceed_factory, error_factory,
                     **_options):   # pragma: doctest no cover
        constraint_iter = iter(self.constraints)
        def chainer(blk, var, *_args, **_kw):
            for constraint in constraint_iter:
                return constraint.inline(blk, var, chainer,
                                         error_factory, **_options)
            else:
                if proceed_factory is not None:
                    return proceed_factory(blk, var, *_args, **_kw)
        return chainer(blk, var, proceed_factory, error_factory, **_options)

    def __repr__(self):     # pragma: doctest no cover
        return '(%s)' % ' & '.join(
            '%r' % constraint for constraint in self.constraints)

BWConstrainable.all_factory = BWAllConstraint

class BWSubConstraint(BWConstraint):
    def __init__(self, constraint):
        self.constraint = self.constraint_from_object(constraint)

class BWNotConstraint(BWSubConstraint):
    def check(self, obj, **_options):
        return not self.constraint.check(obj, **_options)
BWConstrainable.is_not_factory = BWNotConstraint

class BWValueConstraint(BWConstraint):
    def __init__(self, *values):
        self.values = values

class BWTypeConstraint(BWValueConstraint):
    def __init__(_self, *_values, **_kw):
        super(BWTypeConstraint, _self).__init__(*_values)
        _self.registry = _kw.pop('registry', BWObject)

    @cached
    def converted_values(self):
        registry = self.registry
        return tuple(value if isinstance(value, type) else registry[value]
                     for value in self.values)

    def check(self, obj, **_options):
        return isinstance(obj, self.converted_values)

    def __repr__(self):         # pragma: doctest no cover
        values = tuple(value.__name__ if isinstance(value, type)
                            else '%s.%s' % (self.registry.__name__, value)
                       for value in self.values)
        return '<isa %r>' % '|'.join(values)
BWConstrainable.isa_factory = BWTypeConstraint

class BWRoleConstraint(BWValueConstraint):
    def __init__(_self, *_values, **_kw):
        super(BWRoleConstraint, _self).__init__(*_values)
        _self.registry = _kw.pop('registry', BWObject)

    @cached
    def converted_values(self):
        registry = self.registry
        return tuple(value if isinstance(value, type) else registry[value]
                     for value in self.values)

    def check(self, obj, **_options):
        roles = getattr(obj, '__bwroles__', ())
        for value in self.converted_values:
            if value in roles:
                return True
        else:
            return False

    def __repr__(self):     # pragma: doctest no cover
        values = tuple(value.__name__ if isinstance(value, type)
                            else '%s.%s' % (self.registry.__name__, value)
                       for value in self.values)
        return '<does %r>' % '|'.join(values)
BWConstrainable.does_factory = BWRoleConstraint

class BWEqualToConstraint(BWValueConstraint):
    def check(self, obj, **_options):
        return obj in self.values

    def __repr__(self):     # pragma: doctest no cover
        return '<in %r>' % '|'.join(repr(value) for value in self.values)
BWConstrainable.equal_to_factory = BWEqualToConstraint

class BWNotEqualToConstraint(BWValueConstraint):
    def check(self, obj, **_options):
        return obj not in self.values

    def __repr__(self):     # pragma: doctest no cover
        return '<not in %r>' % '|'.join(repr(value) for value in self.values)
BWConstrainable.not_equal_to_factory = BWNotEqualToConstraint

class BWGreaterThanConstraint(BWValueConstraint):
    def check(self, obj, **_options):
        return all(obj > value for value in self.values)

    def __repr__(self):     # pragma: doctest no cover
        return '<GT %r>' % '&'.join(repr(value) for value in self.values)
BWConstrainable.greater_than_factory = BWGreaterThanConstraint

class BWLessThanConstraint(BWValueConstraint):
    def check(self, obj, **_options):
        return all(obj < value for value in self.values)

    def __repr__(self):     # pragma: doctest no cover
        return '<LT %r>' % '&'.join(repr(value) for value in self.values)
BWConstrainable.less_than_factory = BWLessThanConstraint

class BWGreaterThanOrEqualToConstraint(BWValueConstraint):
    def check(self, obj, **_options):
        return all(obj >= value for value in self.values)

    def __repr__(self):     # pragma: doctest no cover
        return '<GTE %r>' % '&'.join(repr(value) for value in self.values)
BWConstrainable.greater_than_or_equal_to_factory = \
    BWGreaterThanOrEqualToConstraint

class BWLessThanOrEqualToConstraint(BWValueConstraint):
    def check(self, obj, **_options):
        return all(obj <= value for value in self.values)

    def __repr__(self):     # pragma: doctest no cover
        return '<LTE %r>' % '&'.join(repr(value) for value in self.values)
BWConstrainable.less_than_or_equal_to_factory = \
    BWLessThanOrEqualToConstraint

class BWFunctionConstraint(BWConstraint):
    def __init__(_self, _func, *_args, **_kw):
        _self.options = _kw.pop('__options__', False)
        _self.func = _func
        _self.args = _args
        _self.kw = _kw

    def check(_self, _obj, **_options):
        if _self.options:   # pragma: doctest no cover
            return _self.func(_obj, *_self.args, **dict(_self.kw, **_options))
        else:
            return _self.func(_obj, *_self.args, **_self.kw)
BWConstrainable.ok_factory = BWFunctionConstraint

STRING = BWConstraint.register(ISA(str, unicode), 'STRING')
NUMBER = BWConstraint.register(ISA(int, float, complex), 'NUMBER')
REAL = BWConstraint.register(ISA(int, float), 'REAL')

class BWMember(BWAnyConstraint):
    '''Support for type-checking members.

    =======
    Summary
    =======

    Sometimes it is useful to validate the types of instance members to
    make sure they are behaving correctly during set or construction.  To
    facilitate this, bullwinkle provides a BWMember class that is used to
    define type-checking properties that do other useful things as well:

    * Builder of values from other attributes
    * Caching of internal methods or functions
    * Type conversion of contructed/set values
    * Indirection of members and methods via attribute

    =======
    Example
    =======

    >>> class TagWrapper(BWSmartObject):
    ...     tag = BWMember('STRING', into=str)
    ...     endtag = BWMember(bool, into=bool, default=True)
    ...     def __call__(self, s):
    ...         if self.endtag:
    ...             return '<%s>%s</%s>' % (self.tag, s, self.tag)
    ...         else:
    ...             return '<%s>%s' % (self.tag, s)
    >>> wrapper = TagWrapper('b')
    >>> wrapper('Hello')
    '<b>Hello</b>'

    >>> class Point(BWSmartObject):
    ...     x = BWMember('NUMBER', into=float, builder='default_value')
    ...     y = BWMember('NUMBER', into=float, builder='default_value')
    ...     default_value = lambda s: 0

    >>> p = Point()
    >>> p.x
    0
    >>> p.y
    0

    ==========
    Delegation
    ==========

    Members can also define delegation properties, which are used to access
    inner attribtues and values through outer members.  For instance,
    suppose we have the a FilePath class that has an open method:

    >>> class FilePath(BWSmartObject):   # Can also be regular Python object
    ...     filename = BWMember('STRING', into=str)
    ...     def open(self, mode='r'):
    ...         # Replace fileobj value with open(...) for real.
    ...         return '<file: %s>' % self.filename

    Now the File class wants to be able to access the filename as well:

    >>> class File(BWSmartObject):      # At least a BWObject is required
    ...     fileobj = BWMember(into=str, required=False,
    ...                        builder=lambda s: s.filepath.open())
    ...     filepath = BWMember(FilePath, into=FilePath)
    ...     filename = filepath.delegate()

    >>> f = File(filename='test')   # Initializing filepath via delegation.
    >>> f.fileobj
    '<file: test>'
    >>> f.filename      # No explicit indirection needed!
    'test'

    Delegation can be translated via alternative attributes as well:

    >>> class Inner(BWSmartObject):
    ...     label = BWMember(into=str)
    >>> class Outer(BWSmartObject):
    ...     label = BWMember(into=str)
    ...     inner = BWMember(into=Inner)
    ...     inner_label = inner.delegate('label')

    >>> outer = Outer(label='hello', inner_label='test')
    >>> outer.inner.label
    'test'

    '''

    delegates = ()

    def __init__(self, *_constraints, **_options):
        extra, kw = self.init(**_options)
        super(BWMember, self).__init__(*(_constraints + extra), **kw)

    def init(self, default=NULL, builder=None, #handles=None,
                   required=True, into=(), lazy=None, **_kw):

        self.required = required

        #self.handles = handles

        if builder is not None:
            if getattr(builder, '__bwbuilder_wantsdefault__', False):
                default = BUILDER(builder, default)
            else:
                default = BUILDER(builder)
        self.default = default

        if lazy is None:
            lazy = getattr(default, '__bwbuilder__', False)
        self.lazy = lazy

        if into and not isinstance(into, (tuple, list)):
            into = (into,)
        self.into = into

        _extra = []
        types = tuple(item for item in self.into if isinstance(item, type))
        if types:
            _extra.append(ISA(*types))

        return tuple(_extra), _kw

    def delegate(self, gateway=None, cache=True, name=None):
        if name is None:
            def builder(cls, name, value):
                return self.delegate(name if gateway is None else gateway,
                                     cache=cache, name=name)
            return BWObject.binder(builder)
        else:
            def alias(target):
                return getattr(getattr(target, self.name), gateway)
            self.delegates += ((name, gateway),)
            return cached(alias) if cache else property(alias)

    def __bwbind__(self, cls, name, value):
        self.name = name
        getter = self.make_getter(name)
        setter = self.make_setter(name)
        remover = self.make_remover(name)

        # NOTE: I don't like the handles= forms, they make things less
        # readable.  This code will allow for them though if needed in the
        # future.

        #if self.handles:
        #    if isinstance(self.handles, (list, tuple, set)):
        #        for handle in self.handles:
        #            delegate = self.delegate(handle, name=handle)
        #            setattr(cls, handle, delegate)
        #    elif isinstance(self.handles, dict):
        #        for outer, inner in self.handles.iteritems():
        #            delegate = self.delegate(inner, name=outer)
        #            setattr(cls, outer, delegate)
        #    else:
        #        delegate = self.delegate(self.handles, name=self.handles)
        #        setattr(cls, self.handles, delegate)

        @cls.init_inline
        def setup_member(cls, blk, required=None, set_attr=True, name=name):
            if required is None:
                required = self.required
            if self.delegates:
                blk.kwargs[name] = NULL
                for dest in self.into:
                    # TODO: Handle multiple dests, exclude last try:
                    try_blk = blk
                    args = []
                    for varname, delegate in self.delegates:
                        args.append('%s=%s' % (delegate, varname))
                        member = getattr(dest, delegate).__bwmember__
                        member.__bwinit_maker__(cls, blk,
                                                name=varname,
                                                required=False,
                                                set_attr=False)
                    if_blk = try_blk.add(
                        'if %s is %s:' % (name, blk.anon(NULL)))
                    if_blk.append('%s = %s(%s)' %
                                   (name, blk.anon(dest),
                                    ', '.join(args)))
            if self.lazy:
                blk.kwargs[name] = NULL
                if_blk = blk.add('if %s is not %s:' % (name, blk.anon(NULL)))
                if_blk.append('_self.%s = %s' % (name, name))
            else:
                if self.delegates or not required:
                    blk.kwargs[name] = NULL
                elif not self.delegates and self.default is NULL:
                    blk.args.append(name)
                else:
                    blk.kwargs[name] = self.default
                if set_attr:
                    blk.append('_self.%s = %s' % (name, name))
        self.__bwinit_maker__ = setup_member

        t = type(name, (object,), {})
        if getter:
            t.__get__ = getter
        if setter:
            t.__set__ = setter
        if remover:     # pragma: doctest no cvoer
            t.__delete__ = remover
        t.__bwmember__ = self
        return t()

    def make_getter(self, name):
        fn = CodeBlock('def get_%s(self, target, cls=None):' % name)
        self.build_getter(fn, name)
        if self.lazy:
            builder = getattr(self.default, '__bwbuilder__', False)
            if builder:
                fn.append('return %s(target)' % fn.anon(self.default))
            else:
                fn.append('return %s' % fn.anon(self.default))
        if fn:
            return getattr(fn.result, 'get_' + name)
        else:
            return None

    def build_getter(self, fn, name):
        pass

    def make_setter(self, name):
        fn = CodeBlock('def set_%s(self, target, value):' % name)
        self.build_setter(fn, name)
        if fn:
            return getattr(fn.result, 'set_' + name)
        else:
            return None

    def build_setter(self, fn, name):
        def success(blk, var):
            blk.append('target.__dict__[%r] = value' % name)
        def error(blk, var, msg):
            # Try into cases if provided.
            for into in self.into:
                with blk.add('try:') as try_blk:
                    try_blk.add('value = %s(value)'
                                % blk.anon(getattr(into, '__name__'), into))
                    try_blk.add('target.__dict__[%r] = value' % name)
                blk = blk.add('except (TypeError, ValueError):')

            blk.append('raise TypeError('
                            '("Cannot set %r to %%r: " + %r) %% value)'
                       % (name, msg))
        self.inline(fn, 'value', success, error)

    def make_remover(self, name):
        fn = CodeBlock('def del_%s(self, target):' % name)
        self.build_remover(fn, name)
        if fn:
            return getattr(fn.result, 'del_' + name)
        else:
            return None

    def build_remover(self, fn, name):
        pass

    @staticmethod
    def builder(_name, *_args, **_kw):
        if isinstance(_name, basestring):
            def builder(self):
                obj = getattr(self, _name)
                if type(obj) is MethodType:
                    return obj(*_args, **_kw)
                else:
                    return obj
        elif isinstance(_name, type):
            builder = lambda s: _name()
        else:
            builder = lambda s: _name(s)
        builder.__name__ = '<%s builder>' % _name
        builder.__bwbuilder__ = True
        return builder

class BWConstMember(BWMember):
    def make_setter(self, name):
        return None

    def make_remover(self, name):
        return None

MEMBER = BWMember
CONST = BWConstMember
BUILDER = MEMBER.builder

class BWRole(BWObject):
    '''
    >>> class Painter(BWRole):
    ...     paint = BWRole.required_method('ctx')

    >>> @Painter.apply
    ... class Widget(BWObject):
    ...     def paint(self, ctx):
    ...         print "Widget paint", ctx

    >>> w = Widget()
    >>> w in Painter
    True

    >>> w.paint('CTX')
    Widget paint CTX

    Roles can be applied to instances as well:

    >>> class OtherWidget(object):
    ...     def paint(self, ctx):
    ...         print "Other widget", ctx
    >>> o = OtherWidget()
    >>> Painter.apply(o) is o
    True
    >>> o in Painter
    True

    In addition, the required methods can be attached to the object itself
    rather than it's type:

    >>> class ExtraWidget(object):
    ...     pass
    >>> e = ExtraWidget()
    >>> e in -Painter
    True
    >>> Painter.apply(e)
    Traceback (most recent call last):
        ...
    TypeError: Role 'Painter' requires 'paint' in 'ExtraWidget instance'
    >>> e.paint = lambda ctx: 'Extra paint ' + ctx
    >>> Painter.apply(e) is e
    True
    >>> e in Painter
    True

    '''

    __bwrequires__ = ()

    @classmethod
    def apply(role, target, instance=None):
        roledict = dict((name, value)
                        for name, value in role.__dict__.iteritems()
                        if name not in BWRole.__dict__)
        if isinstance(target, type):
            checked = target if instance is None else instance
            for requirement in role.__dict__.get('__bwrequires__', ()):
                requirement(checked)
            for base in role.__bases__:
                for requirement in getattr(base, '__bwrequires__', ()):
                    requirement(checked)
            roles = (role,) + getattr(target, '__bwroles__', ())
            return type(target.__name__, (target,),
                        dict(roledict, __bwroles__=roles))
        else:
            roled = role.apply(type(target), target)
            target.__class__ = roled
            return target

    @classmethod
    def __get_bwconstraint__(cls):
        return DOES(cls)

    @classmethod
    def requires(cls, *fns):
        cls.__bwrequires__ += fns
        return cls

    @classmethod
    def required_method(cls, *args):
        @cls.binder
        def checker(role, name, value):
            @cls.requires
            def attrcheck(target):
                value = getattr(target, name, NULL)
                if value is NULL:
                    targetname = (target.__name__
                                  if isinstance(target, type)
                                  else '%s instance' % type(target).__name__)
                    raise TypeError('Role %r requires %r in %r'
                                    % (role.__name__, name, targetname))
                else:
                    func = getattr(value, 'im_func', value)
                    code = getattr(func, 'func_code', None)
                    if code is None:
                        targetname = (target.__name__
                                      if isinstance(target, type)
                                      else '%s instance'
                                           % type(target).__name__)
                        raise TypeError(
                            'Role %r expects a method %r in %r'
                            % (role.__name__, name, targetname))
                    names = code.co_varnames[:code.co_argcount]
                    for arg in args:
                        if arg not in names:
                            targetname = (target.__name__
                                          if isinstance(target, type)
                                          else '%s instance'
                                               % type(target).__name__)
                            raise TypeError(
                                'Role %r requires %r to accept %r in %r'
                                % (role.__name__, name, arg, targetname))
            return NULL
        return checker

    @classmethod
    def required(cls, *constraints):
        constraints = ALL(*constraints)
        @cls.binder
        def checker(role, name, value):
            @cls.requires
            def attrcheck(target):
                value = getattr(target, name, NULL)
                if value is NULL:
                    raise TypeError('Role %r requires %r in %r'
                                    % (role.__name__, name, target.__name__))
                elif value not in constraints:
                    raise TypeError('Role %r requires %r for %e in %r'
                                    % (role.__name__, name,
                                        constraints, target.__name__))
        return checker

