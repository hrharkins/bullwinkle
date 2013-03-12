
from wrapper import cached
from container import NOT_FOUND, ChainedDict
import sys

class CodeBlock(list):
    '''Manages an abstract scaffold for building code on-the-fly,

    =======
    Summary
    =======

    A code block contains a tree of objects that can produce Python code
    It is a list of contained strings (statements), sequences (anonymous
    subsections), and other code blocks.  Code blocks also maintain a set of
    variables that are pertainent to the block to be provided during
    compilation.

    =======
    Example
    =======

    >>> with CodeBlock() as blk:
    ...     blk.append('print "Hello %s" % who')
    >>> print blk
    print "Hello %s" % who
    >>> blk.run(who='world')
    Hello world
    >>> fn_blk = CodeBlock('def f(who):', blk)
    >>> fn_blk.result.f('world')
    Hello world

    ==============
    Block Contents
    ==============

    Lists, tuples, strings, generators, functions, and other code blocks
    can be added to code blocks.

    >>> cb = CodeBlock()
    >>> cb.append('print "Hello"')
    >>> cb.append(['print "Doctor"'])
    >>> cb.append(iter(('print "Name"', 'print "Continue"')))
    >>> cb.append(lambda cb: 'print "Yesterday"')
    >>> cb.append(CodeBlock('print "Tomorrow"'))
    >>> cb.run()
    Hello
    Doctor
    Name
    Continue
    Yesterday
    Tomorrow

    ============
    Inner Blocks
    ============

    Blocks can also be defined with or without a statement.  Without a
    statement, the contents are attached in-line (no indentation):

    >>> fn = CodeBlock('def f():')
    >>> blk = fn.block()
    >>> blk.append("print('Hello')")
    >>> print fn
    def f():
        print('Hello')
    >>> fn.result.f()
    Hello

    With a statment, indentation only occurs if it ends with a colon:

    >>> fn = CodeBlock('def f(who):')
    >>> blk = fn.block('if who == "world":')
    >>> blk.append('print("Hello %s" % who)')
    >>> print fn
    def f(who):
        if who == "world":
            print("Hello %s" % who)
    >>> fn.result.f('world')
    Hello world
    >>> fn.result.f('someone else')

    When applying a statment, positional arguments are used to fill-in the
    blanks provided by the statement:

    >>> fn = CodeBlock('def f(who):')
    >>> blk = fn.block('if who == "%s":', 'world')
    >>> blk.append('print("Hello %s" % who)')
    >>> print fn
    def f(who):
        if who == "world":
            print("Hello %s" % who)
    >>> fn.result.f('world')
    Hello world
    >>> fn.result.f('someone else')

    And any keyword arguments are added to variables:

    >>> fn = CodeBlock('def f(who):')
    >>> blk = fn.block('if who == test:', test='world')
    >>> blk.append('print("Hello %s" % who)')
    >>> print fn
    def f(who):
        if who == test:
            print("Hello %s" % who)
    >>> fn.result.f('world')
    Hello world
    >>> fn.result.f('someone else')

    ============
    Code Globals
    ============

    Blocks can define both named and anonymouse variables.  Named variables
    are defined via the define method:

    >>> cb = CodeBlock('print("Hello %s" % who)')
    >>> cb['who'] = 'world'
    >>> cb['who']
    'world'
    >>> cb.run()
    Hello world

    Deleting them is as expected, except no error is thrown if the key
    wasn't defined:

    >>> del cb['who']
    >>> del cb['who']

    Or as keyword arguments to the run method:

    >>> cb = CodeBlock('print("Hello %s" % who)')
    >>> cb.run(who='world')
    Hello world

    Anonymous variables are defined by not providing a name argument, with
    some care provided for string substitutions:

    >>> cb = CodeBlock()
    >>> cb.append('print("Hello %%s" %% %s)' % cb.anon('world'))
    >>> cb.run()
    Hello world

    To make debugging easier a name can also be provided:

    >>> cb.anon('who', 'world')     # doctest: +ELLIPSIS
    '__..._who'

    ==============
    The add Method
    ==============

    To make block creation simpler, a generic front-end for append and
    block is provided, "add".  It takes an optional parameterized
    statement, optional format args, and optional keywords and either calls
    append or block() as (seemingly) appropriate.

    >>> cb = CodeBlock('def fn(who):')
    >>> with CodeBlock('def fn(who):') as cb:
    ...     cb.add('print("Hello %s" % who)')
    ...     with cb.add('if who == %s:', cb.anon('world')) as if_blk:
    ...         if_blk.add('print("Big hello!")')
    ...     # Watch for the subtle difference when passing parameters --
    ...     # they are treated as format parms to the statement.
    ...     cb.add('print(msg + " " + %s)', 'who', msg='Goodbye')
    >>> cb.result.fn('anyone')
    Hello anyone
    Goodbye anyone
    >>> cb.result.fn('world')
    Hello world
    Big hello!
    Goodbye world

    ==================
    result and extract
    ==================

    The result attribute provides access to the result sans keyword
    argument context.  To retrieve variables using a keyword context use
    the extract() method:

    >>> cb = CodeBlock('x = "Hello " + y')
    >>> cb.extract('x', y='world')
    'Hello world'

    '''

    def __init__(_self, _statement=None, *_insert, **_vars):
        super(CodeBlock, _self).__init__(_insert)
        _self.statement = _statement
        _self.vars = dict(**_vars)

    def __getitem__(self, name, NOT_FOUND=NOT_FOUND):
        value = self.get(name, NOT_FOUND)
        if value is NOT_FOUND:  # pragma: doctest no cover
            raise KeyError(name)
        else:
            return value

    def __setitem__(self, name, value):
        self.vars[name] = value

    def __delitem__(self, name):
        self.vars.pop(name, None)

    def get(self, name, default=None):
        return self.vars.get(name, default)

    @cached
    def result(self):
        d = {}
        self.__addvars__(d)
        try:
            exec self.compiled in d
        except Exception, e:    # pragma: doctest no cover
            raise EvalError(self), None, sys.exc_info()[2]
        class CompiledResult(object):
            @cached
            def __getitem__(self):
                return self.__dict__.__getitem__
        o = CompiledResult()
        o.__dict__.update(d)
        return o

    def extract(self, name, **_kw):
        d = {}
        self.__addvars__(d)
        d.update(_kw)
        try:
            exec self.compiled in d
        except Exception, e:    # pragma: doctest no cover
            raise EvalError(self), None, sys.exc_info()[2]
        return d[name]

    @cached
    def compiled(self):
        try:
            return compile(str(self), '', 'exec')
        except Exception, e:    # pragma: doctest no cover
            raise CompileError(self), None, sys.exc_info()[2]

    def run(self, **_kw):
        d = {}
        self.__addvars__(d)
        d.update(_kw)
        try:
            exec self.compiled in d
        except Exception, e:    # pragma: doctest no cover
            raise EvalError(self), None, sys.exc_info()[2]

    listiter = list.__iter__

    def __iter__(self):
        return self.generate()

    def __addvars__(self, vars):
        for item in self.listiter():
            if isinstance(item, CodeBlock):
                item.__addvars__(vars)
        vars.update(self.vars)

    def generate(self, prefix=''):
        # TODO: Consider inverted implementation where emit receives blocks
        # instead of items to reduce function call count.
        def emit(item, statement=None, prefix=''):
            if statement:
                statement = statement.strip()
                yield prefix + statement
                if statement.endswith(':'):
                    prefix += '    '
                found = False
                for line in emit(item, None, prefix):
                    found = True
                    yield line
                if not found:
                    yield prefix + 'pass'
            else:
                if isinstance(item, CodeBlock):
                    for line in item.generate(prefix=prefix):
                        yield line
                elif isinstance(item, (tuple, list)):
                    for thing in item:
                        for line in emit(thing, prefix=prefix):
                            yield line
                elif isinstance(item, basestring):
                    yield prefix + item
                elif callable(item):
                    for line in emit(item(self), prefix=prefix):
                        yield line
                else:
                    for thing in item:
                        for line in emit(thing, prefix=prefix):
                            yield line
        return emit(self.listiter(), self.get_statement(), prefix)

    def get_statement(self):
        return self.statement

    @cached
    def source(self):
        return '\n'.join(self)

    def __str__(self):
        return self.source

    def add(self, statement=None, *_params, **_kw):
        if not statement or statement.endswith(':'):
            block = self.block(statement, *_params, **_kw)
            return block
        else:
            if _params:
                statement = statement % _params
            self.append(statement)
            if _kw:
                self.vars.update(_kw)

    def block(self, statement=None, *_params, **_kw):
        if statement:
            if _params: # pragma: branch no cover
                statement = statement % _params
            block = CodeBlock(statement)
        else:
            block = CodeBlock()
            statement = None
        self.append(block)
        block.__dict__.update(self.__dict__)
        block.statement = statement
        block.vars = self.vars
        if _kw:
            block.vars.update(_kw)
        return block

    def anon(self, *args):
        if len(args) == 1:
            value = args[0]
            name = '_'
        elif len(args) == 2:
            name, value = args
        else:   # pragma: no doctest coverage
            raise TypeError('anon requires one or two argumetns')
        name = '__%.8X_%s' % (id(value), name)
        self.vars[name] = value
        return name

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        pass

class CompileError(Exception):  # pragma: doctest no cover
    def __init__(self, src):
        self.src = src

    def __str__(self):
        return 'While compiling:\n%s\n' % self.src

class EvalError(Exception): # pragma: doctest no cover
    def __init__(self, src):
        self.src = src

    def __str__(self):
        return 'While evaluating:\n%s\n' % self.src

