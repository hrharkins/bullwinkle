'''
bwmember -- Easy to build type-safe propreties

>>> class MyClass(BWObject):
...     x = member(int, str)
...
>>> c = MyClass(x=5)
>>> c.x
5
>>> c.x = 7
>>> c.x
7
>>> c.x = 'Hello'
>>> c.x
'Hello'
>>> c.x = None
Traceback (most recent call last):
    ...
TypeError: None ('x') must be one of: (int, str)
'''

from bwobject import BWObject
from bwmethod import after_super
from bwcached import cached

class BWMemberProperty(property):
    pass

class BWMember(BWObject):
    ro = False

    def __init__(self, *isa, **_kw):
        self.isa = isa
        self.init(**_kw)

    def init(self, ro=None):
        if ro is not None:
            self.ro = ro

    def __bindclass__(self, cls, name):
        p = BWMemberProperty(self.get_reader(cls, name),
                             self.get_writer(cls, name),
                             self.get_deleter(cls, name))
        p.__initobj__ = self.__initobj__
        return p

    def typecheck(self, obj):
        for check in self.isa:
            if isinstance(obj, check):
                return True
            elif check is None and obj is None:
                return True
        return False

    def __initobj__(self, obj, name, value):
        if not self.typecheck(value):
            raise TypeError('%r (%r) must be one of: (%s)'
                            % (value, name,
                               ', '.join(t.__name__ for t in self.isa)))
        obj.__dict__[name,] = value

    def get_reader(self, cls, name):
        return lambda o: o.__dict__[name,]

    def get_writer(self, cls, name):
        if self.ro:
            return None
        else:
            return lambda o, v: self.__initobj__(o, name, v)

    def get_deleter(self, cls, name):
        if self.ro:
            return None
        else:
            return None

def member(*_args, **_kw):
    return BWMember(*_args, **_kw)

def ro_member(*_args, **_kw):
    _kw.setdefault('ro', True)
    return BWMember(*_args, **_kw)

