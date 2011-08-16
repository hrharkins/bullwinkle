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
<testctx.test.hello.world => 'something'>
>>> del ctx.test['hello.world']

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

>>> root = BWContext('root', x='root_x')
>>> left = BWContext('left', root, y='left_y')
>>> left2 = BWContext(None, left)
>>> right = BWContext('right', root, y='right_y')
>>> bottom = BWContext('bottom', left2, right, y='sub_y')
>>> bottom.x
<bottom.x => 'root_x'>
>>> left2.x
<left{1}.x => 'root_x'>
>>> bottom.a
<bottom.a => :missing:>

Contexts can are BWThrowables (see bwthrowable) and can be retrieved via
BWContext.CURRENT:

>>> rootctx.throw()
>>> BWContext.CURRENT is rootctx
True

To create a new context based on the the current context, create a
BWContext with no name:

>>> +BWContext(None).user
User(roles=('hero', 'flying'), username='superman')

Context variables can also be established at construction time.  If the
name has double-underscores, they will be converted to '.' characters.

>>> ctx = BWContext(None, user__roles__hello='world')
>>> +ctx.user.roles.hello
'world'

References can also be made in an unbound manner by referencing a context
class:

>>> user = BWContext.user
>>> roles = BWContext['user.roles']

These can then be dereferences against a context by calling the references
with the binding context:

>>> user
<user>
>>> +user(rootctx)
User(roles=('hero', 'flying'), username='superman')
>>> +user.roles(rootctx)
('hero', 'flying')
>>> +user['roles.flying'](rootctx)
True
>>> +user
Traceback (most recent call last):
    ...
KeyError: 'user'

Only contexts may be dereferenced in this way:

>>> +user(None)
Traceback (most recent call last):
    ...
TypeError: Unbound ref requires a context

Deleting context variables has the effect of masking base context
declarations:

>>> ctx = BWContext(None)
>>> del ctx.user
>>> print -ctx.user
None
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
            for ref in self._bro:   # pragma: no partial
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
        '''
        Declares the function to be a context property (it will be called
        when referenced).

        >>> ctx = BWContext('test')
        >>> ctx.fn = ctx.property(lambda c: 'hello')
        >>> ctx.fn
        <test.fn => 'hello'>
        '''

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
        return self._self() ** other

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
        value = ~self
        return '<%s.%s => %s>' % (self._ctx._name, self._path,
                                  ':missing:' if value is type(None)
                                                else repr(value))

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

