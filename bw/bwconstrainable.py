
from types import MethodType, FunctionType
FUNC_TYPES = (MethodType, FunctionType)

class BWConstrainable(object):
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
    __bwtypes__ = None

    @classmethod
    def ISA(cls, *options, **_kw):
        _kw.setdefault('registry', cls.__bwtypes__)
        return cls.isa_factory(*options, **_kw)

    @classmethod
    def DOES(cls, *options, **_kw):
        _kw.setdefault('registry', cls.__bwtypes__)
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

