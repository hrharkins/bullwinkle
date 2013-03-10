'''
bwcontext -- A light-weight context manager

A context is a loose collection of information that can be stashed on the
stack to maintain related state.  Each layer of the context stack maintains
its own local storage which appears to containing sub-contexts if the
associated value is not defined at a higher level.

For example, let's create a base context and put some environment-like
information in it:

>>> from bwmember import member, into
>>> class User(BWObject):
...     username = member(str)
...     roles = member(into(tuple, list), default=())
...
...     def __installctx__(self, ctx):
...         ctx.expose(self, 'roles')
...         for role in self.roles:
...             ctx.roles[role] = True
...
>>> rootctx = BWContext('rootctx')
>>> rootctx
<rootctx>
>>> rootctx.user = User(username='superman', roles=('hero', 'flying'))
>>> rootctx.user
<rootctx/user => User(roles=('hero', 'flying'), username='superman')>
>>> 'hero' in +rootctx.user.roles
True
>>> -rootctx.user.roles.hero
True
>>> bool(-rootctx.user.roles.stealthy)
False

In this example, we define a class to contain a user record, attach it to
a context, and access the user roles via the context's reference operator
(+).  There are two operators available to dereference context lookups:

 * + (plus) will raise a KeyError if the path does not exist

 * - (minus) will return None if the path does not exist

 * ~ (tilda) will return type(None) if the path does not exist

Here they are in action:

>>> print +rootctx.var
Traceback (most recent call last):
    ...
KeyError: 'var'
>>> print -rootctx.var
None
>>> print ~rootctx.var
<type 'NoneType'>

The reason for the third tilda (~) form is to allow for cases where None is
a valid return.  type(None) is also a singleton so can be tested for using
is:

>>> ~rootctx.var is type(None)
True

Attribute-based variables cannot begin with an underbar.  Those are
reserved for BWContext internal variables.

>>> rootctx._something
Traceback (most recent call last):
    ...
AttributeError: _something

=======================
=== Naming Contexts ===
=======================

Every context has a name, though in many cases it is inherited from the
parent objects.  The first argument to BWContext's constructor may be the
name which must be either None (for anonymous subcontexts) or a string.
This ensures that some lineage can be maintained for debugging:

>>> root = BWContext('root')
>>> BWContext(BWContext(BWContext(root)))
<root{3}>

However, a name is required for root contexts:

>>> BWContext()
Traceback (most recent call last):
    ...
TypeError: name must be specified for root contexts

=============================
=== Referencing Variables ===
=============================

References can also be made in an unbound manner by referencing a context
class:

>>> user = BWContext.user
>>> roles = BWContext['user.roles']

These can then be dereferences against a context by calling the references
with the binding context:

>>> user
<*BWContext/user>
>>> +(rootctx/user)
User(roles=('hero', 'flying'), username='superman')
>>> +(rootctx/user.roles)
('hero', 'flying')
>>> +(rootctx/user['roles.flying'])
True
>>> +user
Traceback (most recent call last):
    ...
KeyError: 'user'

Only contexts may be dereferenced in this way:

>>> +([]/user)
Traceback (most recent call last):
    ...
TypeError: Ref resolution requires dict, a subclass or instance of BWContext, or None

Requesting a reference of an empty path returns the same subpath:

>>> roles[''] is roles
True
>>> bound = rootctx/roles
>>> bound[''] is bound
True

To get at the underlying context, use the .context attribute.  This may
create lookup the current context if necessary.  This property also exists
on contexts as well as ref so it can be used ubiquitously if needed.

>>> ctx = BWContext('root').throw()
>>> ctx.context is ctx                  # Context self-ref
True
>>> ctx['hello'].context is ctx         # Bound context ref
True
>>> BWContext['hello'].context          # Unbound context ref
<root{1}>

========================================
=== Dereferencing Context References ===
========================================

Although tempting, there is no automatic conversion of references into
objects in the presence of operators (like add, sub, etc).  This is to
provide a uniform approach to accessing referenced items.  The only
exception to this is the power operator due to order of precedence:

>>> ctx = BWContext('temp')
>>> ctx.x = 5
>>> ctx.x ** 2
25

No special oeprators are needed for setting or deleting though.  When
referencing attributes, only one segment is attached at a time.  When
referencing by item, the path may include '.' separators:

>>> ctx = BWContext('testctx')
>>> ctx.test.it = 5
>>> del ctx.test.it
>>> ctx.test['hello.world'] = 'something'
>>> ctx.test['hello.world']
<testctx/test.hello.world => 'something'>
>>> del ctx.test['hello.world']

References (both bound and unbound) can be rebound to other contexts
(including None) using the division operator:

 * None/ref => an unbound ref

    >>> ref = ctx.test
    >>> None/ref
    <*BWContext/test>

 * {}/ref => a bound ref to a new context with that dictionary as a base.

   >>> ref = ctx.test
   >>> dict(test='hello')/ref
   <dict/test => 'hello'>

 * ctx/ref => a ref bound to that context.  The context must be an instance
    of the equivalent unbound type of the reference:

    >>> ref = ctx.test
    >>> other = BWContext('other', test='world')
    >>> other/ref
    <other/test => 'world'>
    >>> class OtherContext(BWContext):
    ...     pass
    >>> other = OtherContext('other')
    >>> oref = other/ref
    >>> ctx/oref
    Traceback (most recent call last):
        ...
    TypeError: Ref resolution requires dict, a subclass or instance of OtherContext, or None

 * ctxclass/ref => an unbound ref to the context class specified.  The
    class must be a subclass of the the equivalent unbound type of the
    reference:

    >>> ref = ctx.test
    >>> BWContext/ref
    <*BWContext/test>
    >>> class OtherContext(BWContext):
    ...     pass
    >>> other = OtherContext('other')
    >>> oref = other/ref
    >>> BWContext/oref
    Traceback (most recent call last):
        ...
    TypeError: Ref resolution requires dict, a subclass or instance of OtherContext, or None

=====================
=== Subcontexting ===
=====================

Subcontexting is a simple matter of using the base context in the
consturctor of another context.  For our example, let's change the
contextual user in effect:

>>> subctx = BWContext(rootctx)
>>> subctx.user
<rootctx{1}/user => User(roles=('hero', 'flying'), username='superman')>
>>> subctx.user = User(username='batman', roles=('hero', 'stealthy'))
>>> subctx.user
<rootctx{1}/user => User(roles=('hero', 'stealthy'), username='batman')>
>>> 'stealthy' in +subctx.user.roles
True
>>> 'flying' in +subctx.user.roles
False
>>> -subctx.user.roles.hero
True
>>> -subctx.user.roles.stealthy
True
>>> bool(-subctx.user.roles.flying)
False

Multiple subcontexting is also legal and follows Python's general rules for
subclassing:

>>> comboctx = BWContext(rootctx, subctx)
>>> comboctx.user
<rootctx{1},rootctx{2}/user => User(roles=('hero', 'stealthy'), username='batman')>
>>> -comboctx.user.roles.hero
True
>>> -comboctx.user.roles.stealthy
True
>>> bool(-comboctx.user.roles.flying)
False

>>> root = BWContext('root', x='root_x')
>>> left = BWContext('left', root, y='left_y')
>>> left2 = BWContext(left)
>>> right = BWContext('right', root, y='right_y')
>>> bottom = BWContext('bottom', left2, right, y='sub_y')
>>> bottom.x
<bottom/x => 'root_x'>
>>> left2.x
<left{1}/x => 'root_x'>
>>> bottom.a
<bottom/a => :missing:>

Contexts can also be created using the call operator() on an existing
context.  This has the same arguments as the constructor but places the
called context as the left-most base for the next context.  For example,
this is equivalent to the above "bottom" case:

>>> bottom = left2('bottom', right, y='sub_y')
>>> bottom.x
<bottom/x => 'root_x'>

======================================
=== Throwing and Catching Contexts ===
======================================

Contexts can are BWThrowables (see bwthrowable) and can be retrieved via
the class property BWContext.CURRENT:

>>> ctx = rootctx.throw()
>>> BWContext.CURRENT is rootctx
True

To create a new context based on the the current context, use the CURRENT
class property:

>>> +BWContext.CURRENT().user
User(roles=('hero', 'flying'), username='superman')

========================
=== Deep Definitions ===
========================

Context variables can also be established at construction time.  If the
name has double-underscores, they will be converted to '.' characters.

>>> ctx = BWContext.CURRENT(user__roles__hello='world')
>>> +ctx.user.roles.hello
'world'

====================
=== Partial Keys ===
====================

In some caes, a prefix key is used to reference an object (which then might
perform additional actions on a subkey):

>>> ctx = BWContext('test')
>>> ctx['test.'] = 'hello'
>>> +ctx.test
'hello'
>>> +ctx.test.it
'hello'
>>> +ctx.test.it.world
'hello'
>>> print -ctx.other
None

Partial keys is a way of placign a context inside of another:

>>> mainctx = BWContext('main')
>>> subctx = BWContext('sub')
>>> mainctx['sub.'] = subctx
>>> subctx.hello = 'world'
>>> mainctx.sub.hello
<main/sub.hello => 'world'>

==========================
=== Deleting Variables ===
==========================

Deleting context variables has the effect of masking base context
declarations:

>>> ctx = BWContext.CURRENT()
>>> del ctx.user
>>> print -ctx.user
None

======================
=== Dynamic values ===
======================

Objects placed in a context that define a __ctxproperty__ attribut will
have that attribute called (as a function or method) upon access by a
context.  The property function will receive the context, the subpath, and
a default value and is responsible for determining the correct value given
those arguments or returning default if inappropriate or not found.

The BWContext .property() method will convert a normal Python function into
an object that produces the described effect.

>>> def printer(ctx, subpath, default):
...     return 'Hello %s' % subpath
...
>>> ctx = BWContext('test-property')
>>> ctx['hello.'] = ctx.property(printer)
>>> ctx.hello.world
<test-property/hello.world => 'Hello world'>

This could be defined in objects as the following:

>>> from bullwinkle import after_super, before_super
>>> class MyPrinter(BWContextInstallable, BWContextProperty):
...     prefix = member(str, default='Hello')
...     exclude = member(str, None, default=None)
...
...     @before_super
...     def ctx_access(self, ctx, subpath, default):
...         if subpath != self.exclude:
...             return '%s %s!' % (self.prefix, subpath)
...
...     @after_super
...     def ctx_install(self, ctx):
...         ctx[''] = self      # All accesses below this go to self too.
...
>>> ctx = BWContext('test-property-object')
>>> ctx.hello = MyPrinter()
>>> ctx.hello.world
<test-property-object/hello.world => 'Hello world!'>

Contrast this with:

>>> ctx = BWContext('test-property-object')
>>> ctx.hello = MyPrinter(exclude='world')
>>> ctx.hello.world
<test-property-object/hello.world => :missing:>

==========================
=== Installing Objects ===
==========================

Objects that define an __installctx__ method will have that method called
when the object is assigned to a context.   This method will receive a
context ref indiciating where the object should be installed.  The
installation occurs on a temporary sub-context which is then merged if the
installation is successful.  Additionally, any variables set in the process
are tracked and removed if del is later invoked on the path.

As noted in the example of the previous section, the BWContextInstallable
base class will call 'ctx_install' instead, making the code slightly more
readable.

Installers can also use the context's "property" method to define property
functions:

>>> class HelloMachine(BWContextInstallable):
...     def ctx_install(self, ctx):
...         ctx[''] = ctx.property(lambda c, s, d: self.helloizer(s))
...
...     def helloizer(self, subpath):
...         return 'Hello %s' % subpath
...
>>> ctx = BWContext('test-install')
>>> ctx.hello = HelloMachine()
>>> ctx.hello.world
<test-install/hello.world => 'Hello world'>

=======================
=== Dynamic getters ===
=======================

The function used to get variables from a storage or reference dictionary
is controlled by the _getter() method.  This method returns a function or
method to get the values based on a key and default value.  The base class
implementation will either:

 * If partial keys are in use in this context, a function that will scan
    those prefixes if the requested key is not in the passed storage.

 * The .get method of the storage passed.

>>> from bullwinkle import filter_super
>>> class MyContext(BWContext):
...     @filter_super
...     def _getter(self, super_getter, storage):
...         def getter(key, default=None):
...             if (isinstance(key, basestring) and
...                 key.startswith('whole_world.')):
...                 return 'hello world'
...             else:
...                 return super_getter(key, default)
...         return getter
...
>>> ctx = MyContext('test')
>>> ctx.whole_world
<test/whole_world => :missing:>
>>> ctx.whole_world.something
<test/whole_world.something => 'hello world'>
>>> sub = BWContext(ctx)
>>> sub.whole_world.something
<test{1}/whole_world.something => 'hello world'>
>>> sub.something_else
<test{1}/something_else => :missing:>

Note that the first example is :missing: because the test is for things
that start with "whole_world.", not just "whole_world".

Any function can be returned by .getter as long as it accepts a key and a
default and can have its __self__ attribute assigned (with the underlying
dictionary).

>>> class BadContext(BWContext):
...     def _getter(self, storage):
...         return [].__getitem__
...
>>> ctx = BadContext('bad')
>>> +ctx.test
Traceback (most recent call last):
    ...
TypeError: _getter function's __self__ must be a dict
>>> sub = BWContext(ctx)
>>> +sub.test
Traceback (most recent call last):
    ...
TypeError: _getter function's __self__ must be a dict

=========================
=== _storage and _ref ===
=========================

Internally, a context flips between _storage and _ref dictionaries
depending on whether another context is referencing this one.  The current
state can be tested by examining the context\'s __dict__.  For a new
context that is unreferenced and has nothing stored, neither _storage nor 
_ref will be available.

>>> ctx = BWContext('test')
>>> '_storage' in ctx.__dict__
False
>>> '_ref' in ctx.__dict__
False

>>> ctx.abc = 'abc, rev 1'
>>> '_storage' in ctx.__dict__
True
>>> '_ref' in ctx.__dict__
False

>>> sub = BWContext(ctx)
>>> sub.abc
<test{1}/abc => 'abc, rev 1'>
>>> '_storage' in ctx.__dict__
False
>>> '_ref' in ctx.__dict__
True

>>> ctx.abc = 'abc, rev 2'
>>> '_storage' in ctx.__dict__
True
>>> '_ref' in ctx.__dict__
False

>>> ctx.abc
<test/abc => 'abc, rev 2'>
>>> sub.abc
<test{1}/abc => 'abc, rev 1'>

'''

from __version__ import *
from bwthrowable import BWThrowable
from bwcached import cached
from bwobject import BWObject
import sys, traceback

NOT_FOUND = type(None)
DELETED = KeyError

class BWContextMeta(getattr(BWThrowable, '__metaclass__', type)):
    def __getattr__(cls, name):
        return BWUnboundContextRef(cls, name.replace('__', '_'))

    def __getitem__(cls, key):
        return BWUnboundContextRef(cls, key)

    @property
    def CURRENT(cls):
        return cls.catch()

class BWContext(BWThrowable):
    __metaclass__ = BWContextMeta
    _varkeys = ()

    def __init__(_self, _name=None, *_basectx, **_kw):
        if isinstance(_name, basestring):
            _self.__dict__.update(_name = _name, _names = (_name,),
                                                 _depths = (0,))
        elif _name is not None:
            _basectx = (_name,) + _basectx
        _self.__dict__['_basectx'] = _basectx
        if not _basectx and _self.__dict__.get('_name') is None:
            raise TypeError('name must be specified for root contexts')
        if _kw:
            for key, value in _kw.iteritems():
                # Init arguments must be strings or Python raises a
                # TypeError.
                _self[key.replace('__', '.')] = value

    def __call__(_self, _name=None, *_others, **_kw):
        return type(_self)(_name, _self, *_others, **_kw)

    @cached
    def _name(self):
        return ','.join('%s{%d}' % (name, depth)
                        for name, depth in zip(self._names, self._depths))

    @cached
    def _names(self):
        result = []
        for base in self._basectx:
            result.extend(base._names)
        return result

    @cached
    def _depths(self):
        result = []
        for base in self._basectx:
            result.extend(d + 1 for d in base._depths)
        return result

    @cached
    def _getters(self):
        if '_ref' in self.__dict__:
            return (self._ref_getfn,) + self._bro
        else:
            # We will invoke storage here to make sure a _getter of some
            # kind is created.
            return (self._storage_getfn,) + self._bro

    @cached
    def _storage(self):
        ref = self.__dict__.pop('_ref', None)
        self.__dict__.pop('_getters', None)
        if ref is None:
            return {}
        else:
            self.__dict__.pop('_ref_getfn', None)
            return dict(ref)

    @cached
    def _storage_getfn(self):
        storage = self._storage
        fn = self._getter(storage)
        if not hasattr(fn, '__self__'):
            fn.__self__ = storage
        elif not isinstance(fn.__self__, dict):
            raise TypeError('_getter function\'s __self__ must be a dict')
        return fn

    @cached
    def _ref(self):
        storage = self.__dict__.pop('_storage', None)
        self.__dict__.pop('_getters', None)
        if storage is None:
            return {}
        else:
            self.__dict__.pop('_storage_getfn', None)
            return storage

    @cached
    def _ref_getfn(self):
        ref = self._ref
        fn = self._getter(ref)
        if not hasattr(fn, '__self__'):
            fn.__self__ = ref
        elif not isinstance(fn.__self__, dict):
            raise TypeError('_getter function\'s __self__ must be a dict')
        return fn

    def _getter(self, storage):
        varkeys = self._varkeys
        if len(varkeys):
            def getter(key, default=None, NOT_FOUND=NOT_FOUND,
                            self=self, varkeys=varkeys, storage=storage):
                obj = storage.get(key, NOT_FOUND)
                subkey = None
                if obj is NOT_FOUND and isinstance(key, basestring):
                    # We've already tested for at least one varkey.
                    for prefix, value in varkeys: # pragma: no partial
                        if key.startswith(prefix):
                            obj = value
                            subkey = key[len(prefix):]
                            break
                    else:
                        obj = default
                return self._getprop(obj, default, subkey)
            return getter
        else:
            return storage.get

    def _getprop(self, obj, default=None, subkey=None):
        propfn = getattr(obj, '__ctxproperty__', None)
        if propfn is True:
            obj = obj(self, subkey, default)
        elif propfn is not None:
            obj = obj.__ctxproperty__(self, subkey, default)
        return obj

    @cached
    def _bro(self):
        bases = self._basectx
        if not bases:
            return ()
        elif len(bases) == 1:
            return (bases[0]._ref_getfn,) + bases[0]._bro
        else:
            return tuple(reversed(self._rbro))

    @cached
    def _rbro(self):
        bases = self._basectx
        if not bases:
            return ()
        elif len(bases) == 1:
            return bases[0]._rbro + (bases[0]._ref_getfn,)
        else:
            ctx = list(bases[-1]._rbro)
            ctx.append(bases[-1]._ref_getfn)
            found = set(id(c) for c in ctx)
            for base in reversed(bases[:-1]):
                for getter in base._rbro:
                    if id(getter) not in found:
                        ctx.append(getter)
                        found.add(id(getter))
                getter = base._ref_getfn
                if id(getter) not in found:
                    ctx.append(getter)
                    found.add(id(getter))
            return tuple(ctx)

    def get(self, key, default=None, NOT_FOUND=NOT_FOUND, DELETED=DELETED):
        # This will always have at least one getter.
        for getter in self._getters:    # pragma: no partial
            obj = getter(key, NOT_FOUND)
            if obj is not NOT_FOUND:
                break
        else:
            obj = default
        if obj is DELETED:
            obj = default
        return self._getprop(obj, default)

    def __getattr__(self, name, NOT_FOUND=NOT_FOUND):
        if name.startswith('_'):
            raise AttributeError(name)
        else:
            return BWBoundContextRef(self, name.replace('__', '.'))

    def __setattr__(self, name, value):
        self[name.replace('__', '.')] = value

    def __delattr__(self, name):
        del self[name.replace('__', '.')]

    def __getitem__(self, key, NOT_FOUND=NOT_FOUND):
        return BWBoundContextRef(self, key.replace('__', '.'))

    def __setitem__(self, key, value, NOT_FOUND=NOT_FOUND):
        uninstall = self.get((key, '__uninstall__'), None)
        if uninstall is not None:
            self._storage.update(uninstall)

        fn = getattr(value, '__installctx__', None)
        if (fn is not None and
            self.get(('__installed__', key, id(value))) is None):

            del self[key]
            install_ctx = self()
            install_ctx._storage['__installed__', key, id(value)] = True
            fn(install_ctx[key])
            uninstall = {}
            for ikey in install_ctx._ref:
                uninstall[ikey] = self.get(ikey, DELETED)
            self._storage.update(install_ctx._ref)
            if install_ctx._varkeys:
                self.__dict__['_varkeys'] = \
                    (self._varkeys + install_ctx._varkeys)
            self._storage[key, '__uninstall__'] = uninstall
            self.__dict__.pop('_storage_getfn', None)
            self.__dict__.pop('_getters', None)

        if isinstance(key, basestring) and key.endswith('.'):
            self.__dict__['_varkeys'] = self._varkeys + ((key, value),)
            self._storage[key[:-1]] = value
            self.__dict__.pop('_storage_getfn', None)
            self.__dict__.pop('_getters', None)
        else:
            self._storage[key] = value

    def __delitem__(self, key):
        uninstall = self.get((key, '__uninstall__'), None)
        if uninstall:
            self._storage.update(uninstall)
        self._storage[key] = DELETED

    @property
    def context(self):
        return self

    def property(self, fn):
        '''
        Declares the function to be a context property (it will be called
        when referenced).

        >>> ctx = BWContext('test')
        >>> ctx.fn = ctx.property(lambda c, s, d: 'hello')
        >>> ctx.fn
        <test/fn => 'hello'>
        '''

        fn.__ctxproperty__ = True
        return fn

    def __repr__(self):
        return '<' + self._name + '>'

    def __ctxproperty__(self, basectx, subpath, default=None):
        return self.get(subpath, default)

class BWContextInstallable(BWObject):
    def __installctx__(self, ctx):
        self.ctx_install(ctx)

    def ctx_install(self, ctx):
        pass

class BWContextProperty(BWObject):
    def __ctxproperty__(self, ctx, subpath, default):
        return self.ctx_access(ctx, subpath, default)

    def ctx_access(self, ctx, subpath, default):
        return default

class BWContextRef(BWObject):
    def __pos__(self, NOT_FOUND=NOT_FOUND):
        obj = self._self(NOT_FOUND)
        if obj is NOT_FOUND:
            raise KeyError(self._path)
        else:
            return obj

    def __invert__(self):
        return self._self(type(None))

    def __neg__(self):
        return self._self()

    def __pow__(self, other):
        return self._self() ** other

    def __rdiv__(self, ctx):
        if ctx is None:
            return BWUnboundContextRef(self._ctxtype, self._path)
        elif isinstance(ctx, dict):
            return BWBoundContextRef(BWContext(type(ctx).__name__, **ctx),
                                     self._path)
        elif isinstance(ctx, self._ctxtype):
            return BWBoundContextRef(ctx, self._path)
        elif isinstance(ctx, type) and issubclass(ctx, self._ctxtype):
            return BWUnboundContextRef(ctx, self._path)
        else:
            raise TypeError(('Ref resolution requires dict, a subclass or ' +
                    'instance of %s, or None') % (self._ctxtype.__name__,))

    def _self(self, default=None):
        return default

    def property(self, fn):
        fn.__ctxproperty__ = True
        return fn

    def expose(self, obj, *members):
        for member in members:
            self[member] = self.property(lambda c, s, p: getattr(obj, member))

class BWBoundContextRef(BWContextRef):
    def __init__(self, ctx, path):
        self.__dict__['_ctx'] = ctx
        self.__dict__['_path'] = path

    def __getattr__(self, name):
        return type(self)(self._ctx, self._path + '.' + name.replace('__', '_'))

    def __setattr__(self, name, value):
        self[name.replace('__', '_')] = value

    def __delattr__(self, name):
        del self[name.replace('__', '_')]

    def __getitem__(self, subpath, NOT_FOUND=NOT_FOUND):
        if subpath:
            return type(self)(self._ctx, self._path + '.' + subpath)
        else:
            return self

    def __setitem__(self, subpath, value):
        # Prevent recursion on ctx[''] = installable
        if subpath or not self._path.endswith('.'):
            self._ctx[self._path + '.' + subpath] = value

    def __delitem__(self, subpath):
        del self._ctx[self._path + '.' + subpath]

    def _self(self, default=None):
        return self._ctx.get(self._path, default)

    def __repr__(self):
        value = ~self
        return '<%s/%s => %s>' % (self._ctx._name, self._path,
                                  ':missing:' if value is type(None)
                                                else repr(value))

    @cached
    def _ctxtype(self):
        return type(self._ctx)

    @cached
    def context(self):
        return self._ctx

class BWUnboundContextRef(BWContextRef):
    def __init__(self, ctxtype, path):
        self.__dict__['_ctxtype'] = ctxtype
        self.__dict__['_path'] = path

    def __getattr__(self, name):
        return type(self)(self._ctxtype,
                          self._path + '.' + name.replace('__', '_'))

    def __getitem__(self, subpath):
        if subpath:
            return type(self)(self._ctxtype, self._path + '.' + subpath)
        else:
            return self

    def __repr__(self):
        return '<*%s/%s>' % (self._ctxtype.__name__, self._path)

    @cached
    def context(self):
        return self._ctxtype(self._ctxtype.CURRENT)

