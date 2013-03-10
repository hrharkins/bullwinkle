
from bwobject import BWObject

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

