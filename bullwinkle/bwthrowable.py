'''
bwthrowable -- throw and catch objects on the stack

Provides a means to send contextual objects to called frames.  Thrown
variables are stored based on their Python type so that they may be caught
either the type of a subtype.

For example, consider an HTTP request class:
>>> class HTTPRequest(BWThrowable):
...     def __init__(self, method, path):
...         self.method = method
...         self.path = path
...

It is often the case that a web framework will define one and want to send
it along as context.  Often it is inconvenient to send the context as
parameters to all called functions, so:

>>> req = HTTPRequest('GET', '/index.html')
>>> req.throw()
HTTPRequest()

Now any function that needs access to the request but cannot acquire it by
parameter can pick it up using .catch():

>>> def controller():
...     req = HTTPRequest.catch()
...     print req.path
...
>>> controller()
/index.html

The throw part can be skipped via with statements:

>>> with HTTPRequest('GET', '/image/pic.png') as req:
...     controller()
...
/image/pic.png

In addition, individual keys can be thrown and caught, though throw() is
optional if the key name is a simple string:

>>> def catcher(name):
...     print catch(name)
...
>>> throw('x', 5)
5
>>> catcher('x')
5
>>> x = 7
>>> catcher('x')
7

=================================
=== The TC Throw-Catch object ===
=================================

A special singleton global, "TC." is available to streamline this further.
Anything assiged to TC, by attribute or item, is thrown().  Anything
accessed via TC, by attribute or item, is catch()'ed:

>>> def catcher(name):
...     return TC[name]
...
>>> TC.x = 5
>>> catcher('x')
5
>>> TC['y'] = 7
>>> catcher('y')
7

>>> class MyThrowable(BWThrowable):
...     pass
...
>>> rug = MyThrowable()
>>> rug.throw()
MyThrowable()
>>> catcher(MyThrowable) is rug
True

==========================
=== Handling not found ===
==========================

catch() will return a default value if the key is not found on the stack:

>>> print catch('xyz', 'NOT HERE')
NOT HERE

BWThrowable, however, has several mix-ins that can alter the resulting in
the case of a catch() miss:

>>> print type(BWAutoThrowable.catch()).__name__
BWAutoThrowable
>>> print BWErrorThrowable.catch()
Traceback (most recent call last):
    ...
BWThrowableNotFoundError

The default BWThrowable will simply return None if not found:

>>> print BWThrowable.catch()
None
'''

from __version__ import *
from bwobject import BWObject
import sys

def throw(key, value, frame=0):
    sys._getframe(frame + 1).f_locals[key] = value
    return value

def catch(key, default=None, NOT_FOUND=KeyError):
    f = sys._getframe(1)
    while f is not None:
        obj = f.f_locals.get(key, NOT_FOUND)
        if obj is not NOT_FOUND:
            return obj
        f = f.f_back
    else:
        return default

class BWThrowableNotFoundError(Exception):
    def __init__(self, cls):
        self.cls = cls

class BWThrowable(BWObject):
    def throw(self, frame=0):
        sys._getframe(frame + 1).f_locals[type(self)] = self
        return self
    __enter__ = throw

    @classmethod
    def catch(cls):
        top = sys._getframe(1)
        for base in cls.__mro__:
            f = top
            while f is not None:
                obj = f.f_locals.get(base)
                if obj is not None:
                    return obj
                else:
                    f = f.f_back
        else:
            return cls.uncaught()

    @classmethod
    def uncaught(self):
        return None

    def __exit__(self, *_args):
        pass

class BWAutoThrowable(BWThrowable):
    @classmethod
    def uncaught(cls):
        args, kw = cls.get_auto_args()
        return cls()

    @classmethod
    def get_auto_args(self):
        return (), {}

class BWErrorThrowable(BWThrowable):
    error_type = BWThrowableNotFoundError

    @classmethod
    def uncaught(cls):
        raise cls.error_type(cls)

class BWThrowCatch(object):
    def __getitem__(self, key):
        if isinstance(key, type):
            return key.catch()
        else:
            return catch(key)

    def __setitem__(self, key, value):
        throw(key, value, 1)

    def __getattr__(self, name):
        return catch(name)

    def __setattr__(self, name, value):
        throw(name, value, 1)

TC = BWThrowCatch()

