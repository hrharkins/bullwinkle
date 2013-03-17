'''
>>> class Base(BWObject):
...     def fn(self):
...         print "Base.fn"
...         return 'Base.result'

>>> class Before(Base):
...     @before_super
...     def fn(self):
...         print "Before.fn"

>>> Before().fn()
Before.fn
Base.fn
'Base.result'

>>> class After(Base):
...     @after_super
...     def fn(self):
...         print "After.fn"

>>> After().fn()
Base.fn
After.fn
'Base.result'

>>> class Around(Base):
...     @around_super
...     def fn(self, super_fn):
...         print "Around.fn (before)"
...         result = super_fn()
...         print "Around.fn (after)"
...         return result

>>> Around().fn()
Around.fn (before)
Base.fn
Around.fn (after)
'Base.result'
'''

from bwobject import BWObject, BWSmartObject
from bwmember import BWMember
from util import wrapper, cached, CodeBlock

@BWObject.positional('fn')
class BWSuperCaller(BWSmartObject):
    fn = BWMember()
    want_args = BWMember(bool, default=False)

    def __bwbind__(self, cls, name, value):
        fnname = cls.__name__ + '_' + name
        blk = CodeBlock('def %s(_self, *_args, **_kw):' % fnname)
        blk.append('result = None')
        self.setup(blk, cls, name)
        #import sys; print >>sys.stderr, blk
        fn = blk.result[fnname]
        fn.__source__ = str(blk)
        fn.__name__ = name
        fn.__doc__ = self.fn.__doc__
        return fn

    def setup(self, blk, cls, name):
        args = ['_self']
        self.setup_args(args, blk, cls, name)
        sub = CodeBlock()
        self.setup_return(sub, cls, name)
        blk.append('value = %s(%s)' % (blk.anon(self.fn), ','.join(args)))
        self.translate_null(blk)
        blk.append(sub)
        blk.append('return result')

    def setup_args(self, args, blk, cls, name):
        if self.want_args:
            args.append('*_args')
            args.append('**_kw')

    def setup_return(self, blk, cls, name):
        pass

    def translate_null(self, blk, var='value', dest='result'):
        blk.add('if %s is type(None): %s = None' % (var, dest))
        blk.add('if %s is not None: %s = %s' % (var, dest, var))

class BWBeforeCaller(BWSuperCaller):
    def setup_return(self, blk, cls, name):
        if_blk = blk.add('if value is None:')
        if_blk.append('value = super(%s, _self).%s(*_args, **_kw)'
                        % (blk.anon(cls), name))
        self.translate_null(if_blk)
        blk.append('return result')

@wrapper
def before_super(fn, want_args=False, **_kw):
    return BWBeforeCaller(fn, want_args=want_args, **_kw)

class BWAfterCaller(BWSuperCaller):
    want_result = BWMember(bool, default=False)

    @before_super(want_args=True)
    def setup(self, blk, cls, name):
        blk.append('value = super(%s, _self).%s(*_args, **_kw)'
                    % (blk.anon(cls), name))
        self.translate_null(blk)

@wrapper
def after_super(fn, **_kw):
    return BWAfterCaller(fn, **_kw)

class BWAroundCaller(BWSuperCaller):
    want_result = BWMember(bool, default=True)

    @before_super(want_args=True)
    def setup_args(self, args, blk, cls, name):
        if self.want_result:
            args.append('super(%s, _self).%s' % (blk.anon(cls), name))

@wrapper
def around_super(fn, want_args=True, **_kw):
    return BWAroundCaller(fn, want_args=want_args, **_kw)

