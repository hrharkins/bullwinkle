import unittest
from bw.util.wrapper import *

class TestWrapper(unittest.TestCase):
    def test_simple(self):
        '''
        Test simplest wrap case.
        '''

        @wrapper
        def simple(fn):
            fn.__here__ = True

        @simple
        def f(): pass

        self.assertEqual(True, f.__here__)

    def test_wrapper(self):
        '''
        Test wrapper wrapping wrapped function (yeah, you read that right).
        '''

        @wrapper
        def bracketed(fn):
            def bracket_wrapper(*_args, **_kw):
                return '[%s]' % (fn(*_args, **_kw))
            return bracket_wrapper

        @bracketed
        def extract(d, name):
            return d.get(name)

        d = { 'hello': 'world' }
        self.assertEqual('[world]', extract(d, 'hello'))

    def test_null_wrapper(self):
        '''
        Ensure that returning type(None) produces None after wrapping.
        '''

        consumed = dict()

        @wrapper
        def consumer(fn):
            consumed[fn.__name__] = fn
            return type(None)

        @consumer
        def hello(): return 'world'

        self.assertEqual('world', consumed['hello']())
        self.assertIsNone(hello)

class WrapperArgTests(unittest.TestCase):
    def test_simple(self):
        'Test zero arguments, but called anyway'

        @wrapper
        def simple(fn):
            fn.__here__ = True

        @simple()
        def f(): pass

        self.assertEqual(True, f.__here__)

    def test_builder_single_arg(self):
        'Test passing single argument to wrapper'

        @wrapper
        def tagger(fn, tag):
            def builder(*_args, **_kw):
                return '<%s>%s</%s>' % (tag, fn(*_args, **_kw), tag)
            return builder

        d = dict(hello='world')
        @tagger('span')
        def lookup(name):
            return d[name]

        self.assertEqual('<span>world</span>', lookup('hello'))

    def test_builder_multi_positional(self):
        'Test passing single argument to wrapper'

        @wrapper
        def tagger(fn, tag, klass=None):
            def builder(*_args, **_kw):
                attr = {}
                if klass:
                    attr['class'] = klass
                argstr = ' '.join('%s="%s"'
                                  % (name, attr[name]) for name in attr)
                if argstr:
                    argstr = ' ' + argstr
                return '<%s%s>%s</%s>' % (tag, argstr, fn(*_args, **_kw), tag)
            return builder

        d = dict(hello='world')
        @tagger('span', 'push-left')
        def lookup(name):
            return d[name]

        self.assertEqual('<span class="push-left">world</span>',
                         lookup('hello'))

    def test_builder_multi_kw(self):
        'Test passing single argument to wrapper'

        @wrapper
        def tagger(fn, tag, klass=None, **attr):
            def builder(*_args, **_kw):
                if klass:
                    attr['class'] = klass
                argstr = ' '.join('%s="%s"'
                                  % (name, attr[name]) for name in attr)
                if argstr:
                    argstr = ' ' + argstr
                return '<%s%s>%s</%s>' % (tag, argstr, fn(*_args, **_kw), tag)
            return builder

        d = dict(hello='world')
        @tagger('span', 'push-left', id="test")
        def lookup(name):
            return d[name]

        self.assertEqual('<span id="test" class="push-left">world</span>',
                         lookup('hello'))

class WrapperAutoTests(unittest.TestCase):
    def test_auto_name_and_doc(self):
        '''
        Verify that functions returned get their names set to the wrapped
        function.
        '''

        @wrapper
        def auto_name(fn):
            def wrap():
                return '[%s]' % fn()
            wrap.__here__ = True
            return wrap

        @auto_name
        def blah():
            'Something'
            return 'blah'

        self.assertEqual(True, blah.__here__)
        self.assertEqual('blah', blah.__name__)
        self.assertEqual('Something', blah.__doc__)

    def test_no_auto_name(self):
        '''
        Turn off auto wrapping (unusual cases)
        '''

        @wrapper(auto_name=False)
        def no_auto_name(fn):
            def wrap():
                return '[%s]' % fn()
            wrap.__here__ = True
            return wrap

        @no_auto_name
        def blah(): return 'blah'

        self.assertEqual(True, blah.__here__)
        self.assertEqual('wrap', blah.__name__)

    def test_no_auto_doc(self):
        '''
        Turn off auto wrapping (unusual cases)
        '''

        @wrapper(auto_doc=False)
        def no_auto_name(fn):
            def wrap():
                'Else'
                return '[%s]' % fn()
            wrap.__here__ = True
            return wrap

        @no_auto_name
        def blah():
            'Something'
            return 'blah'

        self.assertEqual(True, blah.__here__)
        self.assertEqual('Else', blah.__doc__)

class TestCached(unittest.TestCase):
    def test_simple(self):
        'Test simplest caching case'

        class Vector(tuple):
            called = 0

            @cached
            def magnitude(self):
                self.called += 1
                return sum(n ** 2 for n in self) ** 0.5

        v = Vector((3, 4))
        self.assertEqual(v.magnitude, 5.0)
        self.assertEqual(v.magnitude, 5.0)
        self.assertEqual(v.magnitude, 5.0)
        self.assertEqual(v.magnitude, 5.0)
        self.assertEqual(v.magnitude, 5.0)
        self.assertEqual(v.called, 1)

    def test_volatile(self):
        'Test production of volatile values'

        class Loader(object):
            data = None
            called = 0

            @cached
            def load(self):
                self.called += 1
                if self.data is None:
                    return Volatile(None)
                else:
                    return self.data

            @cached
            def thrown(self):
                self.called += 1
                if self.data is None:
                    raise Volatile(None)
                else:
                    return self.data

        l = Loader()
        self.assertIsNone(l.load)
        self.assertIsNone(l.load)
        self.assertIsNone(l.load)
        self.assertIsNone(l.load)
        self.assertIsNone(l.load)
        self.assertEqual(5, l.called)
        l.data = 'Hello'
        self.assertEqual('Hello', l.load)
        self.assertEqual('Hello', l.load)
        self.assertEqual('Hello', l.load)
        self.assertEqual('Hello', l.load)
        self.assertEqual('Hello', l.load)
        self.assertEqual(6, l.called)

        l = Loader()
        self.assertIsNone(l.thrown)
        self.assertIsNone(l.thrown)
        self.assertIsNone(l.thrown)
        self.assertIsNone(l.thrown)
        self.assertIsNone(l.thrown)
        self.assertEqual(5, l.called)
        l.data = 'Hello'
        self.assertEqual('Hello', l.thrown)
        self.assertEqual('Hello', l.thrown)
        self.assertEqual('Hello', l.thrown)
        self.assertEqual('Hello', l.thrown)
        self.assertEqual('Hello', l.thrown)
        self.assertEqual(6, l.called)

