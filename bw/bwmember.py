
from bwobject import BWObject, BWSmartObject
from bw.util import NULL, AnyConstraint, CodeBlock

class BWMember(AnyConstraint):
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

    ========
    Aliasing
    ========

    Simple aliases can be derived from a builder associating with a
    non-method:

    >>> class Person(BWSmartObject):
    ...     name = BWMember('STRING', into=str)
    ...     fullname = BWMember('STRING', builder='name')
    >>> Person(name='test').fullname
    'test'

    ================
    Constant Members
    ================

    Members can be created read-only via the BWConstMember (or CONST
    shortcut):

    >>> class Rooter(int, BWObject):
    ...     root = CONST(float, builder=lambda s: s ** 0.5)
    >>> rooter = Rooter(25)
    >>> rooter.root
    5.0

    ================
    Mutable Defaults
    ================

    To use a mutable type as a default (such as a list or dict), simply use
    the type in the builder=.  This will work for any Python type, but
    should use the BWConstMember (or CONST) member type:

    >>> class Team(BWObject):
    ...     roster = CONST(list, builder=list)
    >>> t = Team()
    >>> t.roster.append('Me')
    >>> t.roster
    ['Me']

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
            # TODO: Add wrapper type for builders that want the default
            # value.
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
        if remover:     # pragma: doctest no cover
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
            else:   # pragma: doctest no cover
                fn.append('return %s' % fn.anon(self.default))
        if fn:
            return getattr(fn.result, 'get_' + name)
        else:       # pragma: doctest no cover
            return None

    def build_getter(self, fn, name):
        pass

    def make_setter(self, name):
        fn = CodeBlock('def set_%s(self, target, value):' % name)
        self.build_setter(fn, name)
        if fn:
            return getattr(fn.result, 'set_' + name)
        else:       # pragma: doctest no cover
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
        self.inline_check(fn, 'value', success, error)

    def make_remover(self, name):
        fn = CodeBlock('def del_%s(self, target):' % name)
        self.build_remover(fn, name)
        if fn:      # pragma: doctest no cover
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
    def make_getter(self, name):
        getter = super(BWConstMember, self).make_getter(name)
        def cacher(self, target, cls=None):
            print self, self.__dict__
            obj = getter(self, target)
            self.__dict__[name] = obj
            return obj
        return cacher

    def make_setter(self, name):
        return None

    def make_remover(self, name):
        return None

MEMBER = BWMember
CONST = BWConstMember
BUILDER = MEMBER.builder

