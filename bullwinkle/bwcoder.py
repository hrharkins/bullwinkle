'''
bwcode -- simplified Python code geenration

Provides means to generate blocks of dynamically generated Python code in
programmatic ways.

>>> block = BWCodeBlock.function('hello', 'who', count=5)
>>> with block.add_for('n', 'range(count)') as for_block:
...     for_block.add_print('"hello"', 'who')
>>> block
# {$ count $} = 5
def hello(who, count={$ count $}):
    for n in range(count):
        print "hello", who
>>> fn = block.object
>>> fn('world')
hello world
hello world
hello world
hello world
hello world
>>> fn('world', 2)
hello world
hello world
>>> fn('world', count=3)
hello world
hello world
hello world

==========================
=== Creating functions ===
==========================

>>> block = BWCodeBlock.function('hello')
>>> block = BWCodeBlock.function('hello', 'pos1', 'pos2')
>>> block = BWCodeBlock.function('hello', 'pos1', 'pos2', kw1='world')

If a variable is both positional and kewyrod, define it twice as such:

>>> block = BWCodeBlock.function('hello', 'pos1', 'pos2', pos2='world')

To access the underlying function, use the object attribute:

>>> block = BWCodeBlock.function('hello')
>>> block.add_print('"Hello world"')
>>> fn = block.object
>>> fn()
Hello world

=================================
=== Creating anonymous blocks ===
=================================

>>> block = BWCodeBlock(None)
>>> block = BWCodeBlock.anonymous()
>>> block = BWCodeBlock('print "Hello"')

Anonymous blocks cannot use the .object attribtue since it would not be
known which object to return:

>>> block.object
Traceback (most recent call last):
    ...
TypeError: Cannot extract from BWCodeBlock

Anonymous blocks can be created inline as well.

>>> with BWCodeBlock.anonymous() as hello_block:
...     hello_block.add_print(repr('Hello'))
>>> with BWCodeBlock.anonymous() as world_block:
...     world_block.add_print(repr('{$ who $}'))
>>> with BWCodeBlock.function('hello_world') as block:
...     # _ignore = for doctests -- not reuqired in practice.
...     _ignore = block.add(hello_block)
...     _ignore = block.add(world_block, who='world')
...     with block.add_anonymous() as anon_block:
...         anon_block.add_print(repr('!!!'))
>>> block
# {$ who $} = 'world'
def hello_world():
    print 'Hello'
    print '{$ who $}'
    print '!!!'

======================
=== Dumping Source ===
======================
>>> block = BWCodeBlock.function('hello')
>>> block.add_print('"Hello world"')
>>> print block
def hello():
    print "Hello world"

=======================
=== Block Variables ===
=======================

>>> block = BWCodeBlock.function('stuff')
>>> block.add_return('{$ xyz $}')
>>> block.object()
Traceback (most recent call last):
    ...
NameError: pseudo-var {$ xyz $} is not defined

>>> block['xyz'] = 'Hello world'
>>> block['xyz']
'Hello world'
>>> block.object()
'Hello world'

>>> del block['xyz']
>>> block.get('xyz') is None
True
>>> block.object()
Traceback (most recent call last):
    ...
NameError: pseudo-var {$ xyz $} is not defined

>>> block.addvars(xyz='Hello world')
>>> block.object()
'Hello world'
>>> block.addvars(dict(xyz='Hello there'))
>>> block.object()
'Hello there'

================
=== Printing ===
================

Special care must be given to quote strings.  All parameters to print are
assumed to be valid Python expressions.

>>> block = BWCodeBlock.function('hello', 'who')
>>> block.add_print('"Hello"', 'who')
>>> hello_fn = block.object
>>> hello_fn('world')
Hello world

========================
=== Returning Values ===
========================

>>> with BWCodeBlock.function('multiply', 'x', 'y') as block:
...     block.add_return('x * y')
...
>>> block.object(3, 5)
15

=======================
=== Yielding Values ===
=======================

>>> with BWCodeBlock.function('gen_values', 'val', count=5) as block:
...     with block.add_for('n', 'xrange(count)') as for_block:
...         for_block.add_yield('val')
...
>>> block
# {$ count $} = 5
def gen_values(val, count={$ count $}):
    for n in xrange(count):
        yield val
>>> list(block.object('hello'))
['hello', 'hello', 'hello', 'hello', 'hello']

===================
=== Assignments ===
===================

>>> with BWCodeBlock.function('setter', 't') as block:
...     block.add_assign(('a', 'b', 'c'), '{$ t $}')
...     block.add_assign('x', '", ".join({$ t $})')
...     block.add_print('{$ a $}', '{$ b $}', '{$ c $}')
>>> block
def setter(t):
    a, b, c = {$ t $}
    x = ", ".join({$ t $})
    print {$ a $}, {$ b $}, {$ c $}

=================
=== If blocks ===
=================

add_if, add_else, and add_elif add the appropriate structures to the block.

>>> with BWCodeBlock.function('compare', 'n', what=5) as block:
...     with block.add_if('n < what') as less_block:
...         less_block.add_return('-1')
...     with block.add_elif('n > what') as greater_block:
...         greater_block.add_return('1')
...     with block.add_else() as equal_block:
...         equal_block.add_return('0')
>>> fn = block.object
>>> fn(2)
-1
>>> fn(7)
1
>>> fn(5)
0

==================
=== For blocks ===
==================

>>> with BWCodeBlock.function('ranger', 'end', start=0) as block:
...     with block.add_for('n',
...                        'range({$ start $}, {$ end $} + 1)') as for_block:
...         for_block.add_yield('{$ n $}')
>>> block
# {$ start $} = 0
def ranger(end, start={$ start $}):
    for n in range({$ start $}, {$ end $} + 1):
        yield {$ n $}

>>> block = BWCodeBlock.anonymous()
>>> block.add_for(('x', 'y'), '{$ d $}.iteritems()')
for x, y in {$ d $}.iteritems():
    pass

====================
=== While blocks ===
====================

>>> with BWCodeBlock.function('ranger', 'end', start=0) as block:
...     block.add_assign('n', '{$ start $}')
...     with block.add_while('{$ n $} <= {$ end $}') as while_block:
...         while_block.add_yield('{$ n $}')
...         while_block.add_statement('n += 1')
>>> block
# {$ start $} = 0
def ranger(end, start={$ start $}):
    n = {$ start $}
    while {$ n $} <= {$ end $}:
        yield {$ n $}
        n += 1

==========================
=== Internal Functions ===
==========================

>>> with BWCodeBlock.function('fib', 'n') as block:
...     with block.add_function('_fib', 'n') as fib_block:
...         with fib_block.add_if('n < 1') as fib_under_one:
...             fib_under_one.add_return('{$ zero $}', zero=0)
...         with fib_block.add_elif('n < 2') as fib_one:
...             fib_one.add_return('{$ one $}', one=1)
...         with fib_block.add_else() as fib_over_one:
...             fib_over_one.add_return('_fib(n - 1) + _fib(n - 2)')
...     block.add_return('_fib(n)')
...
>>> print block
def fib(n):
    def _fib(n):
        if n < 1:
            # {$ zero $} = 0
            return {$ zero $}
        elif n < 2:
            # {$ one $} = 1
            return {$ one $}
        else:
            return _fib(n - 1) + _fib(n - 2)
    return _fib(n)

>>> fib = block.object
>>> [fib(n) for n in range(10)]
[0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

======================
=== Tagging Blocks ===
======================

Sometimes it can be helpfui to find code blocks deep within a hierarchy.
To aid in this, code blocks can be tagged to aid in finding branching
clauses for later population.

>>> with BWCodeBlock.function('hello', 'x') as hello_blk:
...     with hello_blk.add_if('x > 5') as x_over_5:
...         x_over_5.add_tag('x_over_5')
...         x_over_5.add_tag('x_over_0')
...     with hello_blk.add_elif('x > 0') as x_over_0:
...         x_over_0.add_tag('x_over_0')
...     with hello_blk.add_else() as x_under_0:
...         x_under_0.add_tag('x_under_0')
...
>>> for blk in hello_blk.find_tag_multi('x_over_0'):
...     blk.add_print(repr('x > 0'))
>>> for blk in hello_blk.find_tag_multi('x_under_0'):
...     blk.add_print(repr('x < 0'))
>>> for blk in hello_blk.find_tag_multi('x_over_5'):
...     blk.add_print(repr('x > 5'))
>>> fn = hello_blk.object
>>> fn(6)
x > 0
x > 5
>>> fn(2)
x > 0
>>> fn(-2)
x < 0

Anonymous blocks can be tagged during construction:

>>> BWCodeBlock.anonymous('hello')
# Block tagged 'hello'

===============================
=== Testing for Termination ===
===============================

If the block is terminal, in that it is guaranteed to return a value or
raise an exception, the is_terminal attribute will be True.

>>> with BWCodeBlock.anonymous() as returns_blk:
...     returns_blk.add_print(repr('hello'))
...     returns_blk.add_return(repr('world'))
...
>>> returns_blk.is_terminal
True

>>> with BWCodeBlock.anonymous() as open_blk:
...     open_blk.add_print(repr('hello'))
...
>>> open_blk.is_terminal
False

Only if all branches are terminal OR a terminal statement follows branches
will the block be considered terminal:

>>> with BWCodeBlock.anonymous() as returns_blk:
...     returns_blk.add_print(repr('hello'))
...     with returns_blk.add_if('1 > 2') as if_blk:
...         if_blk.add_return('everyone')
...     with returns_blk.add_else() as else_blk:
...         returns_blk.add_return(repr('world'))
...
>>> returns_blk.is_terminal
True

'''

from __version__ import *
from bwcached import cached
import re, sys

# Would love to eat our own dog food here and import around_super, etc, but
# that would lead to an import conflict with bwobject...

argRE = re.compile('\{\$\s*(.*?)\s*\$\}')

class BWCodeBlock(object):
    statement = None
    pass_required = False
    tags = ()
    terminal = False
    branches = False
    last_branch = None

    def __init__(_self, _statement, *_args, **_vars):
        _self._statement = _statement
        _self._args = _args
        if _vars:
            for name, value in _vars.iteritems():
                _self[name] = value

    @cached
    def statement(self):
        return self.make_statement()

    def add_tag(self, *tags):
        self.tags += tags

    def find_tag_multi(self, tag):
        result = []
        self._find_tag(result, tag)
        return result

    def find_tag(self, tag):
        result = self.find_tag_multi(tag)
        if len(result) == 1:
            return result[0]
        elif len(result) == 0:
            return None
        else:
            raise ValueError('multiple results for tag %r' % tag)

    def _find_tag(self, result, tag):
        if tag in self.tags:
            result.append(self)
        if 'block' in self.__dict__:
            for block in self.block:
                block._find_tag(result, tag)
        for peer in self.get_peers(True):
            peer._find_tag(result, tag)

    @cached
    def vars(self):
        return {}

    def make_statement(self):
        if self._statement:
            return self._statement % self._args
        else:
            return None

    def decache(self):
        self.__dict__.pop('vardict', None)
        self.__dict__.pop('evaluated', None)
        self.__dict__.pop('object', None)
        self.__dict__.pop('is_terminal', None)

    @cached
    def is_terminal(self):
        if self.terminal:
            return True
        elif 'block' in self.__dict__:
            all_branches_terminal = True
            for subblk in self.block:
                if subblk.is_terminal:
                    return True
            else:
                return False
        else:
            return False

    def __getitem__(self, name):
        return self.vars[name]

    def __setitem__(self, name, value):
        self.decache()
        self.vars[name] = value

    def __delitem__(self, name):
        self.decache()
        del self.vars[name]

    def get(self, name, default=None):
        return self.vars.get(name, default)

    def addvars(self, *_vardicts, **_kwvars):
        self.decache()
        for vars in _vardicts:
            for name, value in vars.iteritems():
                self[name] = value
        if _kwvars:
            for name, value in _kwvars.iteritems():
                self[name] = value

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        pass

    @cached
    def block(self):
        return []

    def encode(self, indent='', blkvars=None, basevars=(), argRE=argRE):
        levelvars = dict(basevars)
        levelvars.update(self.vardict)

        for tag in self.tags:
            yield indent + '# Block tagged %r' % tag

        for name, value in self.vardict.iteritems():
            rval = repr(value)
            if len(rval) > 40:
                rval = rval[:38] + ' ...'
            yield indent + '# {$ %s $} = %s' % (name, rval)

        def varinsert(match):
            varname = match.group(1)
            varid = '__var_%d__' % len(blkvars)
            try:
                blkvars[varid] = levelvars[varname]
                return varid
            except KeyError:
                raise NameError, 'pseudo-var {$ %s $} is not defined' % varname

        origindent = indent
        if self.statement:
            if blkvars is None:
                statement = self.statement
            else:
                statement = argRE.sub(varinsert, self.statement)
            yield indent + statement
            indent += '    '
        produced_lines = False
        if self.__dict__.get('block'):
            for child in self.block:
                for line in child.encode(indent, blkvars, levelvars):
                    produced_lines = True
                    yield line

        if not produced_lines and self.pass_required:
            yield indent + 'pass'

        for peer in self.get_peers(False):
            for line in peer.encode(origindent, blkvars, levelvars):
                yield line

    def get_peers(self, all_peers):
        return ()

    def __iter__(self):
        return self.encode()

    @classmethod
    def anonymous(_cls, *_tags, **_kw):
        blk = _cls(None, **_kw)
        if _tags:
            blk.add_tag(*_tags)
        return blk

    def add_anonymous(_self, *_tags, **_kw):
        return _self.add(BWCodeBlock.anonymous(*_tags, **_kw))

    @classmethod
    def function(_cls, _name, *_posargs, **_kwargs):
        return BWFunctionBlock(_name, *_posargs, **_kwargs)

    def add_function(_self, _name, *_posargs, **_kwargs):
        return _self.add(_self.function(_name, *_posargs, **_kwargs))

    @cached
    def object(self):
        return self.extract(self.evaluated)

    @cached
    def vardict(self):
        return dict(self.vars)

    @cached
    def evaluated(self):
        blkvars = {}
        src = '\n'.join(self.encode(blkvars=blkvars))
        dest = {}
        exec(src, blkvars, dest)
        return dest

    def extract(self, vars):
        raise TypeError('Cannot extract from %s' % type(self).__name__)

    def add(self, block, **_kw):
        if _kw:
            self.addvars(_kw)
        self.__dict__.pop('evaluated', None)
        self.__dict__.pop('object', None)
        self.block.append(block)
        if block.branches:
            if self.last_branch is None:
                self.last_branch = block
        else:
            self.last_branch = None
        return block

    def add_comment(_self, _comment, **_kw):
        _self.add(BWCodeBlock('# ' + _comment, **_kw))

    def add_statement(_self, _statement, *_args, **_kw):
        _self.add(BWCodeBlock(_statement, *_args, **_kw))

    def add_print(_self, *_items, **_kw):
        _self.add(BWPrintBlock(*_items, **_kw))

    def add_return(_self, *_items, **_kw):
        _self.add(BWReturnBlock(*_items, **_kw))

    def add_yield(_self, _expr, **_kw):
        _self.add(BWYieldBlock(_expr, **_kw))

    def add_assign(_self, _varnames, _expr, **_kw):
        _self.add(BWAssignBlock(_varnames, _expr, **_kw))

    def add_raise(_self, _type, *_args, **_kw):
        _self.add(BWRaiseBlock(_type, *_args, **_kw))

    def add_if(_self, _expr, **_kw):
        return _self.add(BWIfBlock(_expr, **_kw))

    def add_for(_self, _varnames, _iterable, **_kw):
        return _self.add(BWForBlock(_varnames, _iterable, **_kw))

    def add_while(_self, _expr, **_kw):
        return _self.add(BWWhileBlock(_expr, **_kw))

#    def add_elif(_self, _expr, **_kw):
#        return _self.add(BWElifBlock(_expr, **_kw))
#
#    def add_else(_self, **_kw):
#        return _self.add(BWElseBlock(**_kw))

    def add_elif(_self, _expr, **_kw):
        if _self.last_branch is None:
            raise TypeError('Last statement was not branching')
        else:
            return _self.last_branch.add_elif(_expr, **_kw)

    def add_else(_self):
        if _self.last_branch is None:
            raise TypeError('Last statement was not branching')
        else:
            return _self.last_branch.else_blk

    def add_try(_self, **_kw):
        return _self.add(BWTryBlock(**_kw))

    def add_except(_self, _type=None, _var=None, **_kw):
        return _self.add(BWExceptBlock(_type, _var, **_kw))

    def __str__(self):
        return '\n'.join(self)

    def __repr__(self):
        return '\n'.join(self)

class BWReturnBlock(BWCodeBlock):
    terminal = True

    def __init__(_self, *_items, **_kw):
        super(BWReturnBlock, _self).__init__ \
            ('return %s', ', '.join(_items), **_kw)
        _self.items = _items

class BWYieldBlock(BWCodeBlock):
    def __init__(_self, _expr, **_kw):
        super(BWYieldBlock, _self).__init__ \
            ('yield %s', _expr, **_kw)
        _self.expr = _expr

class BWPrintBlock(BWCodeBlock):
    def __init__(_self, *_items, **_kw):
        super(BWPrintBlock, _self).__init__ \
            ('print %s', ', '.join(_items), **_kw)
        _self.items = _items

class BWRaiseBlock(BWCodeBlock):
    terminal = True

    def __init__(_self, _type, *_args, **_kw):
        super(BWRaiseBlock, _self).__init__ \
            ('raise %s(%s)', _type, ', '.join(_args), **_kw)
        _self.type = _type
        _self.args = _args

class BWAssignBlock(BWCodeBlock):
    def __init__(_self, _names, _expr, **_kw):
        if isinstance(_names, (tuple, list)):
            names = tuple(_names)
        else:
            names = (_names,)
        super(BWAssignBlock, _self).__init__ \
            ('%s = %s', ', '.join(names), _expr, **_kw)
        _self.names = names
        _self.expr = _expr

class BWPassingBlock(BWCodeBlock):
    pass_required = True

class BWElsingBlock(BWPassingBlock):
    @cached
    def else_blk(self):
        return BWElseBlock()

    def add_else(self):
        return self.else_blk

    def get_peers(self, all_peers):
        return (super(BWElsingBlock, self).get_peers(all_peers) +
                self.get_else_blocks(all_peers))

    def get_else_blocks(self, all_peers):
        if all_peers or len(self.else_blk.block):
            return (self.else_blk,)
        else:
            return ()

    def is_terminal(self):
        return (super(BWElsingBlock, self).is_terminal and
                self.else_blk.is_terminal)

class BWForBlock(BWElsingBlock):
    branches = True

    def __init__(_self, _varnames, _iterable, **_kw):
        if not isinstance(_varnames, (list, tuple)):
            _varnames = (_varnames,)
        else:
            _varnames = tuple(_varnames)
        super(BWForBlock, _self).__init__ \
            ('for %s in %s:', ', '.join(_varnames), _iterable, **_kw)
        _self.iterable = _iterable
        _self.varnames = _varnames

class BWWhileBlock(BWElsingBlock):
    branches = True

    def __init__(_self, _expr, **_kw):
        super(BWWhileBlock, _self).__init__ \
            ('while %s:', _expr, **_kw)
        _self.expr = _expr

class BWIfBlock(BWElsingBlock):
    branches = True

    def __init__(_self, _expr, **_kw):
        super(BWIfBlock, _self).__init__ \
            ('if %s:', _expr, **_kw)
        _self.expr = _expr

    @cached
    def elif_blks(self):
        return ()

    def add_elif(_self, _expr, **_kw):
        blk = BWElifBlock(_expr, **_kw)
        _self.elif_blks += (blk,)
        return blk

    def get_else_blocks(self, all_peers):
        return (self.elif_blks +
                super(BWIfBlock, self).get_else_blocks(all_peers))

class BWElifBlock(BWPassingBlock):
    def __init__(_self, _expr, **_kw):
        super(BWElifBlock, _self).__init__ \
            ('elif %s:', _expr, **_kw)
        _self.expr = _expr

class BWElseBlock(BWPassingBlock):
    def __init__(_self, **_kw):
        super(BWElseBlock, _self).__init__ \
            ('else:', **_kw)

class BWTryBlock(BWPassingBlock):
    branches = True

    def __init__(_self, **_kw):
        super(BWTryBlock, _self).__init__ \
            ('try:', **_kw)

class BWExceptBlock(BWPassingBlock):
    branches = True

    def __init__(_self, _type=None, _var=None, **_kw):
        if _type is None:
            super(BWExceptBlock, _self).__init__ \
                ('except:', **_kw)
        else:
            if isinstance(_type, (tuple, list)):
                types = tuple(_type)
            else:
                types = (_type,)
            if _var is None:
                super(BWExceptBlock, _self).__init__ \
                    ('except %s:' % ', '.join(_type), **_kw)
            else:
                super(BWExceptBlock, _self).__init__ \
                    ('except %s, %s:' % (', '.join(_type), _var), **_kw)

class BWFunctionBlock(BWPassingBlock):
    kwall = None

    def __init__(_self, _name, *_posargs, **_kwargs):
        _self.name = _name
        _self.posargs = _posargs
        _self.kwargs = dict(_kwargs)
        super(BWFunctionBlock, _self).__init__ \
            (None, **_kwargs)

    def make_statement(self):
        posargs = self.posargs
        kwargs = self.kwargs

        args = []
        vars = {}
        for arg in posargs:
            if arg in kwargs:
                vars[arg] = kwargs.pop(arg)
                args.append('%s={$ %s $}' % (arg, arg))
            else:
                args.append(arg)
        for arg, value in kwargs.iteritems():
            vars[arg] = value
            args.append('%s={$ %s $}' % (arg, arg))
        if self.kwall:
            args.append('**' + self.kwall)
        return 'def %s(%s):' % (self.name, ', '.join(args))

    def extract(self, vars):
        return vars[self.name]

    def add_posarg(self, name):
        self.posargs += (name,)
        self.decache()

    def has_posarg(self, name):
        return name in self.posargs

    def add_kwarg(self, name, value):
        self.kwargs[name] = '{$ %s $}' % name
        self.addvars({ name : value })

    def has_kwarg(self, name):
        return name in self.kwargs

    def set_kwall(self, name):
        self.kwall = name
        self.decache()

