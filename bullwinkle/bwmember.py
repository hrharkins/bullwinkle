'''
bwmember -- Easy to build type-safe propreties

>>> class MyClass(object):
...     x = member(int)
...
>>> c = MyClass(x=5)
>>> c.x
'''

from bwobject import BWObject
from bwmethod import after_super

class BWMember(BWObject):
    def __init__(_self, *_isa, **_kw):
        _self.isa = isa
        _self.kw = _kw
        _self.init(**_kw)

    def init(self, name=None, default=None, lazy=False, required=False):
        self.name = name
        self.default = default
        self.lazy = lazy
        self.required = required

    @cqached
    def isa_fn(self):
        tests = []
        names = {}
        for constraint in self.isa:
            if isinstance(constraint, type):
                tests.append('isinstance(o, %s)' % constraint.__name__)
                names[constraint.__name__] = constraint
        exec 'tester = lambda o: ' + ' or '.join(tests) in names
        tester = names.pop('tester')
        return tester

    def __call__(self, fn):
        return type(self)(*self.isa, **dict(self.kw, default=fn))

    def __bindclass__(self, cls, name):
        cls.__members__ = getattr(cls, '__members__', ()) + \
            (type(self)(*self.isa, **dict(self.kw, name=name)),)
        return self.build_property(cls, name)

    def build_propery(self, cls, name):
        raise NotImplementedError('Cannot make member %r %s'
            % (name, type(self).__name__))

class BWReadOnlyMember(BWMember):
    def build_property(self, cls, name):
        return property(self.get_reader(cls, name))
ro_member = BWReadOnlyMember

class BWReadWriteMember(BWMember):
    def build_property(self, cls, name):
        return property(self.get_reader(cls, name),
                        self.get_writer(cls, name),
                        self.get_deleter(cls, name))
member = BWReadWriteMember

