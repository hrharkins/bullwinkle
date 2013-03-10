
from bw.util import NULL, wrapper, CodeBlock, cached, ChainedDict
from bwconstrainable import *
from bwobject import BWObject

class BWConstraint(BWConstrainable):
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

    __bwtypes__ = ChainedDict(BWObject.__bwtypes__)

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
        _self.registry = _kw.pop('registry', BWConstraint.__bwtypes__)

    @cached
    def converted_values(self):
        registry = getattr(self.registry, '__bwtypes__', self.registry)
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
        _self.registry = _kw.pop('registry', BWConstraint)

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

BWConstrainable.__bwtypes__ = BWConstraint.__bwtypes__
