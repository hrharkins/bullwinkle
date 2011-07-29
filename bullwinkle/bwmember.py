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

