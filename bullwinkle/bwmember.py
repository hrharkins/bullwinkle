'''
bwmember -- Easy to build type-safe propreties

>>> class MyClass(BWObject):
...     x = member(int)
...
>>> c = MyClass(x=5)
>>> c.x
'''

from bwobject import BWObject
from bwmethod import after_super
from bwcached import cached

class BWMember(BWObject):
    def __init__(self, *isa, ro=False):
        self.isa = isa
        self.ro = ro

    def __bindclass__(self, cls, name):
        return property(self.get_reader(cls, name),
                        self.get_writer(cls, name)
                        self.get_deleter(cls, name))

    def __member__(self, obj, name, value):
        if not self.typecheck(obj):
            raise TypeError('%r must be one of %s' % (name, ', '.join(self.isa))

    def get_reader(self, cls, name):
        return None

    def get_writer(self, cls, name):
        if self.ro:
            return None
        else:
            return None

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

