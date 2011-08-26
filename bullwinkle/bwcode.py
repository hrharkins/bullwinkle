'''
bwcode -- simplified Python code geenration

Provides means to generate blocks of dynamically generated Python code in
programmatic ways.

>>> block = BWCodeBlock()
>>> block += block.i_print('thing')
>>> fn = block.as_function('thing')
>>> fn('Hello world')
Hello world
'''

from __version__ import *
from bwobject import BWObject
from bwmethod import around_super, after_super
from bwcached import cached

class BWEncodable(BWObject):
    @cached
    def source(self):
        dest = []
        vars = {}
        self.encode(dest, indent, vars)
        return '\n'.join(dest)

    def encode(self, dest, indent, vars):
        pass

class BWCodeNode(BWEncodable):
    @around_super
    def __init__(self, super_fn, code, *_args, **_kw):
        super_fn()
        self.code = code % _args
        self.kw = _kw

    def encode(self, dest, indent, vars):
        if self.code:
            code = self.code
            dest.append(indent + code)

    def __repr__(self):
        return '<%s %r>' % (type(self).__name__, self.code)

class BWCodeBlock(BWEncodable):
    @around_super
    def __init__(self, super_fn, nodes=()):
        super_fn()
        self.nodes = nodes

    @after_super
    def encode(self, dest, indent, vars):
        for node in self:
            node.encode(dest, indent + '     ')

    def __add__(self, other):
        if isinstance(other, BWCodeNode):
            return type(self)(self.nodes + (other,))
        else:
            return type(self)(self.nodes + other.nodes)

    def i_print(_self, _expr, **_vars):
        return BWCodeNode('print (%s)', _expr, **_vars)

    def as_function(_self, _name, *_varargs, **_kwargs):
        return BWBlockNode('def %s(%s)', _name, ', '.join(_varargs)) + _self

class BWBlockNode(BWCodeNode, BWCodeBlock):
    pass

