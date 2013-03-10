'''Manages the structured checking of variable state.

=======
Summary
=======

=======
Example
=======

Consider these two BWObject classes:

>>> class Chocolate(object): pass
>>> class PeanutButter(object): pass

To look for one or the other we can simply use the in operator on a ISA():

>>> Chocolate() in ISA(Chocolate)
True
>>> Chocolate() in ISA(PeanutButter)
False
>>> PeanutButter() in ISA(Chocolate)
False
>>> PeanutButter() in ISA(PeanutButter)
True

To invert, we *could* use Python's not operator, but there are inlining
advantages to using unary -:

>>> PeanutButter() in -ISA(Chocolate)
True
>>> PeanutButter() in ~ISA(Chocolate)     # Also works
True
>>> PeanutButter() not in ISA(Chocolate)  # Works, but not recommended.
True

To look for any of different options, use bitwise or (|) or ANY_OF():

>>> PeanutButter() in (ISA(Chocolate) | ISA(PeanutButter))
True
>>> Chocolate() in ANY_OF(Chocolate, PeanutButter)
True

Finally, the opposite applies to ALL:

>>> PeanutButter() in (ISA(Chocolate) & ISA(PeanutButter))
False
>>> Chocolate() in ALL_OF(Chocolate, PeanutButter)
False
>>> class PeanutButterCup(Chocolate, PeanutButter):
...     pass
>>> PeanutButterCup() in ALL_OF(Chocolate, PeanutButter)
True

Once a constraint is formed, algebraic operators can take effect:

>>> 5 in ISA(int) | float
True
>>> 7 in float | ISA(int)
True

Additionally, comparisons of value can also be made via various functions:

>>> 'Hello' in ANY_OF('Hello', 'world')
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

Or via the "C" constraint builder:

>>> (5 in (C == 5), 5 in (C == 7))
(True, False)

These can also be grouped:

>>> 5 in ISA(int) & LT(7) & GT(3)
True

====================
Constraint Functions
====================

Although constraints can be checked directly it is sometimes handy to
conver them to first class Python functions.  This can be done via the
cached function property:

>>> fn = ANY_OF(int, str).checker
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
(NEVER, ALWAYS)
>>> 5 in NEVER | int
True
>>> 5.0 in ALWAYS & float
True

These are expected to be used rarely but are included for completeness.

'''

from consts import NULL, NOT_CONVERTED
from code import CodeBlock
from wrapper import cached

class Constrainable(object):
    def constrain(self, other):
        if isinstance(other, Constraint):
            return other
        elif isinstance(other, type):
            return TypeConstraint(other)
        else:
            return ValueConstraint(other)

    def __or__(self, other):
        return AnyConstraint(self, self.constrain(other))

    def __ror__(self, other):
        return self.constrain(other) | self

    def __and__(self, other):
        return AllConstraint(self, other)

    def __rand__(self, other):
        return self.constrain(other) & self

    def __neg__(self):
        return NoneConstraint(self)

    def __invert__(self):
        return -self

class OrGroupable(Constrainable):
    def __or__(self, other):
        other = self.constrain(other)
        cls = self.orGroupClass(other)
        if cls is None:
            return super(AllGroupable, self).__or__(other)
        else:
            return cls(*(self.comparisons + other.comparisons))

    def orGroupClass(self, other):
        if type(self) is type(other):
            return type(self)

class AndGroupable(Constrainable):
    def __and__(self, other):
        other = self.constrain(other)
        cls = self.andGroupClass(other)
        if cls is None:
            return super(AndGroupable, self).__or__(other)
        else:
            return cls(*(self.comparisons + other.comparisons))

    def andGroupClass(self, other):
        if type(self) is type(other):
            return type(self)

class NullConstraint(Constrainable):
    '''
    Factory for constraints.  The constant "C" instantiates this class and
    can be used for convenient defintion of constraints.

    >>> anyof = (C == 5) | (C == 7) | (C == 9)
    >>> noneof = (C != 5) & (C != 7) & (C != 9)
    >>> anyof
    (C == 5) | (C == 7) | (C == 9)
    >>> noneof
    (C != 5) & (C != 7) & (C != 9)
    >>> 5 in anyof
    True
    >>> 5 in noneof
    False
    >>> 6 in anyof
    False
    >>> 6 in noneof
    True
    >>> typeof = C.isa(int, str)
    >>> 5 in typeof
    True
    >>> 'hello' in typeof
    True
    >>> 5.0 in typeof
    False
    >>> 9 in (C > 7)
    True
    >>> 9 in (C > 9)
    False
    >>> 9 in (C >= 9)
    True
    >>> 5 in (C < 3)
    False
    >>> 5 in (C < 5)
    False
    >>> 5 in (C <= 5)
    True
    >>> converter = C.isa(int)
    >>> converter(5)
    5
    >>> converter(5.0)
    5
    >>> converter('5')
    5
    >>> converter('hello')
    Traceback (most recent call last):
        ...
    TypeError: Could not convert 'hello' to C.isa(int)
    '''
    def __or__(self, other):
        return self.constrain(other)

    def __ror__(self, other):
        return self.constrain(other)

    def __eq__(self, other):
        return ValueConstraint(other)

    def __ne__(self, other):
        return NotValueConstraint(other)

    def __lt__(self, other):
        return LessThanConstraint(other)

    def __gt__(self, other):
        return GreaterThanConstraint(other)

    def __le__(self, other):
        return LessThanOrEqualToConstraint(other)

    def __ge__(self, other):
        return GreaterThanOrEqualToConstraint(other)

    def isa(self, *types):
        return TypeConstraint(*types)

    def into(self, *types):
        return IntoConstraint(*types)
C = NullConstraint()
EQ = C.__eq__
NE = C.__ne__
LT = C.__lt__
GT = C.__gt__
LE = LTE = C.__le__
GE = GTE = C.__ge__

class Constraint(Constrainable):
    def __init__(self, *comparisons, **_config):
        self.comparisons = comparisons
        self.configure(**_config)

    def configure(self):
        pass

    def __call__(self, value, **_kw):
        if self.check(value):
            return value
        result = self.convert(value, NOT_CONVERTED, **_kw)
        if result is NOT_CONVERTED:
            raise TypeError('Could not convert %r to %s' % (value, self))
        elif self.check(result):
            return result
        else:
            raise TypeError('Covnerted value %r from %r does not match %s'
                            % (result, value, self))

    def __contains__(self, value):
        return self.check(value)

    def check(self, value, **_kw):      # pragma: doctest no cover
        raise NotImplementedError('check is not implemented on %r' % self)

    def convert(self, value,
                      invalid=NOT_CONVERTED,
                      **_kw):           # pragma: doctest no cover
        if self.check(value):
            return value
        else:
            return invalid

    def __str__(self):
        return repr(self)

    @cached
    def checker(self):
        fn = CodeBlock('def checker(value):')
        def success(blk, var):
            blk.append('return True')
        def failure(blk, var, msg):
            blk.append('return False')
        self.inline_check(fn, 'value', success, failure)
        return fn.result.checker

    @cached
    def converter(self):
        fn = CodeBlock('def converter(value):')
        self.inline_convert(fn, 'value')
        return fn.result.checker

    def inline_check(self, blk, var, success=None, failure=None, negate=None):
        blk = blk.block()
        if success is None:
            success = getattr(blk, 'success', None)
        if failure is None:
            failure = getattr(blk, 'failure', None)
        if negate is None:
            negate = getattr(blk, 'negate', False)
        blk.success = success
        blk.failure = failure
        blk.negate = negate
        self.build_inline_check(blk, var, negate, success, failure)
        if success is None:
            if failure is None:
                pass
            else:
                self.build_inline_check(blk, var, True, failure, success)
        else:
            self.build_inline_check(blk, var, False, success, failure)

    def build_inline_check(self, blk, var, negate, success, failure):
        expr = self.inline_check_expression(blk, var, negate)
        blk.append('# %s' % self)
        if_blk = blk.add('if %s:' % expr)
        success(if_blk, var)
        if failure is not None:
            else_blk = blk.add('else:')
            if negate:
                failure(else_blk, var, 'was %r' % self)
            else:
                failure(else_blk, var, 'was not %s' % self)

    def inline_check_expression(self, blk, var, negate):
        return '%s %s(%s)' % ('not' if negate else '',
                              blk.anon(self.check), var)

class NeverConstraint(Constraint):
    'Permits no objects or conditions.'

    def check(self, value, **_kw):
        return False

    def __repr__(self):
        return 'NEVER'

NEVER = NeverConstraint()

class AlwaysConstraint(Constraint):
    'Permits all objects and conditions.'

    def check(self, value, **_kw):
        return True

    def __repr__(self):
        return 'ALWAYS'

ALWAYS = AlwaysConstraint()

class TypeConstraint(Constraint, OrGroupable):
    '''Checks for instance or class conformance to type.

    >>> c = TypeConstraint(int)
    >>> 5 in c
    True
    >>> 7.0 in c
    False
    >>> c(5.0)
    5

    >>> c = TypeConstraint(int, float)
    >>> 5 in c
    True
    >>> 7.0 in c
    True
    >>> 'hello' in c
    False
    >>> c('5.0')
    5.0
    >>> c('hello')
    Traceback (most recent call last):
        ...
    TypeError: Could not convert 'hello' to C.isa(int, float)
    '''

    def check(self, value, **_kw):
        if isinstance(value, type):
            return issubclass(value, self.comparisons)
        else:
            return isinstance(value, self.comparisons)

    def convert(self, value, invalid=NULL, **_kw):
        if isinstance(value, type):
            if issubclass(value, self.comparisons):
                return value
            else:
                return invalid
        else:
            for factory in self.comparisons:
                try:
                    return factory(value, **_kw)
                except Exception:
                    pass
            else:
                return invalid

    def __repr__(self):
        return 'C.isa(%s)' % ', '.join(c.__name__ for c in self.comparisons)

ISA = TypeConstraint

class ValueConstraint(Constraint, OrGroupable):
    '''Checks for equality with one or more values.

    >>> c = ValueConstraint(5, 6, 9)
    >>> 5 in c
    True
    >>> 3 in c
    False
    >>> c(5)
    5
    >>> c(3)
    Traceback (most recent call last):
        ...
    TypeError: Could not convert 3 to <value 5|6|9>
    '''

    def check(self, value, **_kw):
        return value in self.comparisons

    def __str__(self):
        return '<value %s>' % '|'.join(map(repr, self.comparisons))

    def __repr__(self):
        return ' | '.join('(C == %s)' % repr(c) for c in self.comparisons)

class NotValueConstraint(Constraint, AndGroupable):
    '''Checks for lack of equlity with any of the specified values.
    '''

    def check(self, value, **_kw):
        return value not in self.comparisons

    def __str__(self):
        return '<value %s>' % '|'.join(map(repr, self.comparisons))

    def __repr__(self):
        return ' & '.join('(C != %s)' % repr(c) for c in self.comparisons)

class LessThanConstraint(Constraint, AndGroupable):
    '''Checks for a value to be greater than any values provided.
    '''

    def check(self, value, **_kw):
        return value < min(self.comparisons)

    def __repr__(self):
        return ' & '.join('(C < %s)' % repr(c) for c in self.comparisons)

class GreaterThanConstraint(Constraint, AndGroupable):
    '''Checks for a value to be greater than any values provided.
    '''

    def check(self, value, **_kw):
        return value > max(self.comparisons)

    def __repr__(self):
        return ' & '.join('(C > %s)' % repr(c) for c in self.comparisons)

class LessThanOrEqualToConstraint(Constraint, AndGroupable):
    '''Checks for a value to be greater than any values provided.
    '''

    def check(self, value, **_kw):
        return value <= min(self.comparisons)

    def __repr__(self):
        return ' & '.join('(C <= %s)' % repr(c) for c in self.comparisons)

class GreaterThanOrEqualToConstraint(Constraint, AndGroupable):
    '''Checks for a value to be greater than any values provided.
    '''

    def check(self, value, **_kw):
        return value >= max(self.comparisons)

    def __repr__(self):
        return ' & '.join('(C >= %s)' % repr(c) for c in self.comparisons)

class Subconstraint(Constraint):
    def __init__(self, *comparisons, **config):
        super(Subconstraint, self)\
            .__init__(*(self.constrain(c) for c in comparisons), **config)

class AnyConstraint(Subconstraint, OrGroupable):
    def check(self, value, **_kw):
        if not self.comparisons:
            return True
        for comparison in self.comparisons:
            if comparison.check(value):
                return True
        else:
            return False

    def __neg__(self):
        return NoneConstraint(*self.comparisons)

    def __str__(self):
        return '<any %s>' % '|'.join(map(str, self.comparisons))

ANY_OF = AnyConstraint

class NotAllConstraint(Subconstraint, OrGroupable):
    def check(self, value, **_kw):
        if not self.comparisons:
            return True
        for comparison in self.comparisons:
            if not comparison.check(value):
                return True
        else:
            return False

    def __neg__(self):
        return AllConstraint(*self.comparisons)

    def __str__(self):
        return '<any %s>' % '|'.join(map(str, self.comparisons))

NOT_ALL_OF = NotAllConstraint

class AllConstraint(Subconstraint, AndGroupable):
    def check(self, value, **_kw):
        if not self.comparisons:
            return True
        for comparison in self.comparisons:
            if not comparison.check(value):
                return False
        else:
            return True

    def __neg__(self):
        return NotAllConstraint(*self.comparisons)

    def __str__(self):
        return '<any %s>' % '|'.join(map(str, self.comparisons))

ALL_OF = AllConstraint

class NoneConstraint(Subconstraint, AndGroupable):
    def check(self, value, **_kw):
        if not self.comparisons:
            return True
        for comparison in self.comparisons:
            if comparison.check(value):
                return False
        else:
            return True

    def __str__(self):
        return '<any %s>' % '|'.join(map(str, self.comparisons))

    def __neg__(self):
        return AnyConstraint(*self.comparisons)

NONE_OF = NoneConstraint
