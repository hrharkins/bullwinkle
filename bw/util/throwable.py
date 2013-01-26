'''Manages transporting data across the call stack.

=======
Summary
=======

It is frequently useful to define a global that is contextually relevant
only within a given call stack.  Such contextual data can be associated via
this module through the use of throw() and catch().

=======
Example
=======

A common contextual variable for web servers is a User object.  For this
example, we'll assume a user has some string based gruop names to check:

>>> @thrown
... class User(object):
...     def __init__(self, username, *groups):
...         self.username = username
...         self.groups = frozenset(groups)
...
>>> @wrapper
... def restricted(fn, *groups):
...     groups = frozenset(groups)
...     @catcher(User)
...     def protector(user, *_args, **_kw):
...         if not user.groups >= groups:
...             username = user.username
...             opname = fn.__name__
...             raise NotAllowed('%s not allowed to %s' % (username, opname))
...         else:
...             return fn(*_args, **_kw)
...     return protector
>>> class NotAllowed(Exception): pass

Now let's define some hypothetical rights and users:

>>> rights = ('read', 'write', 'delete')
>>> guest = User('guest')               # No rights
>>> admin = User('admin', *rights)       # All rights
>>> viewer = User('viewer', 'read')
>>> editor = User('editor', 'read', 'write')

Next, let's protect a function such that only a valid user can access
it:

>>> @restricted('read')
... @catcher(user=User)     # Magically adds user kw argument.
... def read_news(user):
...     print "%s READING" % user.username

>>> @restricted('write')
... @catcher(user=User)
... def write_news(user):
...     print "%s WRITING" % user.username

>>> @restricted('delete')
... @catcher(user=User)
... def delete_news(user):
...     print "%s DELETING" % user.username

Finally, let's see who can do what:

>>> for user in (guest, viewer, editor, admin):
...     for op in (read_news, write_news, delete_news):
...         try:
...             throw(user)
...             op()
...         except NotAllowed, e:
...             print e
guest not allowed to read_news
guest not allowed to write_news
guest not allowed to delete_news
viewer READING
viewer not allowed to write_news
viewer not allowed to delete_news
editor READING
editor WRITING
editor not allowed to delete_news
admin READING
admin WRITING
admin DELETING

==============
Missed Catches
==============

If the key is not found on the stack the default is returned.

>>> catch('something') is None
True

To throw an exception, provide an exception type as the default:

>>> catch('something', KeyError)
Traceback (most recent call last):
    ...
KeyError: 'something'

============================
Catching Everything of a Key
============================

To catch all instances of a key, use the catchiter() and iterate through
the result or convert to a list:

>>> def return_all(key):
...     return list(catchiter(key))
>>> def insert_key(key, nextvalue=None, *values):
...     if nextvalue is not None:
...         throw(key, nextvalue)
...         return insert_key(key, *values)
...     else:
...         return return_all(key)
>>> insert_key('hello', 'everyone', 'out', 'there')
['there', 'out', 'everyone']

This can also be written as catchall(), which returns a tuple:

>>> def return_all(key):
...     return catchall(key)
>>> insert_key('hello', 'everyone', 'out', 'there')
('there', 'out', 'everyone')

====================
Specializing the Key
====================

Classes that are thrown can specify the key they want to use by setting
__throwable_key__ or by decorating with @thrown as shown above.  If no key
is provided, the class itself is used as a key.

'''

from wrapper import wrapper
from container import NOT_FOUND
import sys

def throw(key, value=NOT_FOUND, frame=0):
    if value is NOT_FOUND:
        value = key
        key = type(key)
    if isinstance(key, type):
        key = getattr(key, '__throw_key__', key)
    sys._getframe(frame + 1).f_locals[key] = value

def thrown(cls):
    cls.__throw_key__ = cls
    return cls

def catch(key, default=None, frame=0, cls=None, NOT_FOUND=NOT_FOUND):
    if cls is None and isinstance(key, type):
        cls = key
        key = getattr(key, '__throw_key__', key)
    f = sys._getframe(frame + 1)
    while f is not None:
        obj = f.f_locals.get(key, NOT_FOUND)
        if (obj is NOT_FOUND
            or (cls is not None and not isinstance(obj, cls))):
            f = f.f_back
        else:
            return obj
    else:
        if isinstance(default, type) and issubclass(default, Exception):
            raise default(key)
        else:
            return default

def catchiter(key, default=None, frame=0, cls=None, NOT_FOUND=NOT_FOUND):
    f = sys._getframe(frame + 1)
    while f is not None:
        obj = f.f_locals.get(key, NOT_FOUND)
        if obj is not NOT_FOUND and (cls is None or isinstance(obj, cls)):
            yield obj
        f = f.f_back

def catchall(key, default=None, frame=0, cls=None, NOT_FOUND=NOT_FOUND):
    return tuple(catchiter(key, default, frame, cls, NOT_FOUND))

@wrapper
def catcher(_fn, *_names, **_map):
    def mitt(*_args, **_kw):
        _preargs = ()
        for name in _names:
            obj = catch(name, NOT_FOUND)
            if obj is not NOT_FOUND:    # pragma: branch no cover
                _preargs += (obj,)
        for name in _map:
            obj = catch(_map[name], NOT_FOUND)
            if obj is not NOT_FOUND:    # pragma: branch no cover
                _kw[name] = obj
        return _fn(*(_preargs + _args), **_kw)
    return mitt

