
from wrapper import cached

class CodeBlock(list):
    '''Manages an abstract scaffold for building code on-the-fly,

    =======
    Summary
    =======

    A code block is a single entry within a tree of Python code that can be
    managed (and eventually compiled, printed, etc).  A code block is a
    list of contained strings (statements), sequences (anonymous
    subsections), and other code blocks.  Code blocks also maintain a set of
    variables that are pertainent to the block to be provided during
    compilation.

    =======
    Example
    =======

    >>> blk = CodeBlock()
    >>> blk.append('print "Hello %s" % who')
    >>> print blk
    print "Hello %s" % who
    >>> blk.run(who='world')
    Hello world
    >>> fn_blk = CodeBlock('def f(who):', blk)
    >>> fn_blk['f']('world')
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

    '''

    def __init__(_self, _statement=None, *_insert, **_vars):
        super(CodeBlock, _self).__init__(_insert)
        _self.statement = _statement

    def __getitem__(self, name):
        return self.extract(name)

    def extract(self, name, **_kw):
        d = _kw
        exec self.compiled in d
        return d[name]

    @cached
    def compiled(self):
        return compile(str(self), '', 'exec')

    def run(self, **_kw):
        exec self.compiled in _kw

    listiter = list.__iter__

    def __iter__(self):
        return self.generate()

    def generate(self, prefix=''):
        # TODO: Consider inverted implementation where emit receives blocks
        # instead of items to reduce function call count.
        def emit(item, statement=None, prefix=''):
            if statement:
                statement = statement.strip()
                yield prefix + statement
                if statement.endswith(':'):
                    prefix += '    '

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

