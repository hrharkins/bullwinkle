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
>>> rootctx.user = User(username='superman', roles=('hero', 'flying'))
>>> rootctx.user
<rootctx.user => User(roles=('hero', 'flying'), username='superman')>
>>> 'hero' in +rootctx.user.roles
True
>>> -rootctx.user.roles.hero
True
>>> bool(-rootctx.user.roles.stealthy)
False

In this example, we define a class to contain a user record, attach it to
a context, and access the user roles via the context's reference operator
(+).  There are two operators available to dereference context lookups:

 * + (plus) will throw a KeyError if the path does not exist

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

Although tempting, there is no automatic conversion of references into
objects in the presence of operators (like add, sub, etc).  This is to
provide a uniform approach to accessing referenced items.

Subcontexting is a simple matter of using the base context in the
consturctor of another context.  For our example, let's change the
contextual user in effect:

>>> subctx = BWContext(None, rootctx)
>>> subctx.user
<rootctx{1}.user => User(roles=('hero', 'flying'), username='superman')>
>>> subctx.user = User(username='batman', roles=('hero', 'stealthy'))
>>> subctx.user
<rootctx{1}.user => User(roles=('hero', 'stealthy'), username='batman')>
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

>>> comboctx = BWContext(None, rootctx, subctx)
>>> comboctx.user
<rootctx{1},rootctx{2}.user => User(roles=('hero', 'stealthy'), username='batman')>
>>> -comboctx.user.roles.hero
True
>>> -comboctx.user.roles.stealthy
True
>>> bool(-comboctx.user.roles.flying)
False
'''

from __version__ import *
from bwthrowable import BWThrowable
from bwcached import cached
from bwobject import BWObject
import sys

NOT_FOUND = type(None)
DELETED = KeyError

class BWContextMeta(getattr(BWThrowable, '__metaclass__', type)):
    def __getattr__(cls, name):
        return BWUnboundContextRef(name.replace('__', '_'))

    def __getitem__(cls, key):
        return BWUnboundContextRef(key)

    @property
    def CURRENT(cls):
        return cls.catch()

class BWContext(BWThrowable):
    __metaclass__ = BWContextMeta
    _ctxname = None

    def __init__(_self, _name, *_basectx, **_kw):
        if not _name and not _basectx:
            _basectx = (None,)
        _self.__dict__['_basectx'] = \
            tuple(_self.catch() if base is None else base
                  for base in _basectx)
        if _name is not None:
            _self.__dict__['_ctxname'] = _name
            _self.__dict__['_names'] = (_name,)
            _self.__dict__['_depths'] = (0,)
        if _kw:
            for name, value in _kw.iteritems():
                _self[name.replace('__', '.')] = value

    @cached
    def _name(self):
        name = self._ctxname
        if name:
            return name
        else:
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
    def _storage(self):
        ref = self.__dict__.pop('_ref', None)
        if ref is None:
            return {}
        else:
            return dict(ref)

    @cached
    def _ref(self):
        storage = self.__dict__.pop('_storage', None)
        if storage is None:
            return {}
        else:
            return storage

    @cached
    def _bro(self):
        bases = self._basectx
        if not bases:
            return ()
        elif len(bases) == 1:
            return (bases[0]._ref,) + bases[0]._bro
        else:
            return tuple(reversed(self._rbro))

    @cached
    def _rbro(self):
        bases = self._basectx
        if not bases:
            return ()
        elif len(bases) == 1:
            return bases[0]._rbro + (bases[0]._ref,)
        else:
            ctx = list(bases[-1]._rbro)
            ctx.append(bases[-1]._ref)
            found = set(id(c) for c in ctx)
            for base in reversed(bases[:-1]):
                for ref in base._rbro:
                    if id(ref) not in found:
                        ctx.append(ref)
                        found.add(id(ref))
                ref = base._ref
                if id(ref) not in found:
                    ctx.append(ref)
                    found.add(id(ref))
            return tuple(ctx)

    def get(self, key, default=None, NOT_FOUND=NOT_FOUND, DELETED=DELETED):
        obj = self._ref.get(key, NOT_FOUND)
        if obj is NOT_FOUND:
            for ref in self._bro:
                obj = ref.get(key, NOT_FOUND)
                if obj is not NOT_FOUND:
                    break
            else:
                obj = default
        if obj is DELETED:
            obj = default
        while getattr(obj, '__ctxproperty__', False):
            obj = obj(self)
        return obj

    def __getattr__(self, name, NOT_FOUND=NOT_FOUND):
        return BWBoundContextRef(self, name.replace('__', '.'))

    def __setattr__(self, name, value):
        self[name.replace('__', '.')] = value

    def __delattr__(self, name):
        del self[name.replace('__', '.')]

    def __getitem__(self, key, NOT_FOUND=NOT_FOUND):
        return BWBoundContextRef(self, key.replace('__', '.'))

    def __setitem__(self, key, value, NOT_FOUND=NOT_FOUND):
        fn = getattr(value, '__installctx__', None)
        if fn is not None:
            del self[key]
            install_ctx = type(self)(None, self)
            fn(install_ctx[key])
            uninstall = {}
            for ikey in install_ctx._ref:
                uninstall[ikey] = self.get(ikey, DELETED)
            self._storage.update(install_ctx._ref)
            self._storage[key, 'uninstall'] = uninstall
        self._storage[key] = value

    def __delitem__(self, key):
        uninstall = self.get((key, 'uninstall'), None)
        if uninstall:
            self._storage.update(uninstall)
        self._storage[key] = DELETED

    def property(self, fn):
        fn.__ctxproperty__ = True
        return fn

    def __repr__(self):
        return '<' + self._name + '>'

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
        return +self ** other

    def _self(self, default=None):
        return default

    def property(self, fn):
        fn.__ctxproperty__ = True
        return fn

    def expose(self, obj, *members):
        for member in members:
            self[member] = self.property(lambda c: getattr(obj, member))

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
        return type(self)(self._ctx, self._path + '.' + subpath)

    def __setitem__(self, subpath, value):
        self._ctx[self._path + '.' + subpath] = value

    def __delitem__(self, subpath):
        del self._ctx[self._path + '.' + subpath]

    def _self(self, default=None):
        return self._ctx.get(self._path, default)

    def __repr__(self):
        return '<%s.%s => %s>' % (self._ctx._name, self._path, +self)

class BWUnboundContextRef(BWContextRef):
    def __init__(self, path):
        self.__dict__['_path'] = path

    def __getattr__(self, name):
        return type(self)(self._path + '.' + name.replace('__', '_'))

    def __getitem__(self, subpath):
        return type(self)(self._path + '.' + subpath)

    def __call__(self, ctx):
        if isinstance(ctx, BWContext):
            return BWBoundContextRef(ctx, self._path)
        else:
            raise TypeError('Unbound ref requires a context')

    def __repr__(self):
        return '<%s>' % (self._path)

