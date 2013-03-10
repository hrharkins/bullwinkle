
from bw.util import NULL, wrapper, CodeBlock, cached, ChainedDict
from bw.util import Constrainable
#from bwconstrainable import BWConstrainable, ISA
from types import MethodType

class BWMeta(type, Constrainable):
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
    __bwtypes__ = {},
    __get_bwconstraint__ = classmethod(lambda c: ISA(c)),
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

