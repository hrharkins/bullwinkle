
import unittest
from bw.util.throwable import (throw, catch, thrown,
                               catcher, catchiter, catchall)

class TestThrown(unittest.TestCase):
    def test_simple(self):
        def f(key):
            return catch(key)
        throw('hello', 'world')
        self.assertEqual('world', f('hello'))

    def test_class_throw(self):
        class Test(object):
            def __init__(self, msg):
                self.msg = msg

        def f(key):
            return catch(key)
        throw(Test('hello'))
        self.assertEqual('hello', f(Test).msg)

    def test_thrown(self):
        @thrown
        class Test(object):
            def __init__(self, msg):
                self.msg = msg

        class Sub(Test):
            pass

        def f(key):
            return catch(key)

        throw(Sub('hello'))
        self.assertEqual('hello', f(Test).msg)

    def test_default(self):
        self.assertIsNone(catch('not_found'))

    def test_exception(self):
        with self.assertRaises(KeyError):
            catch('not_found', KeyError)

    def test_catchiter(self):
        def return_all(key):
            return list(catchiter(key))
        def insert_key(key, nextvalue=None, *values):
            if nextvalue is None:
                return return_all(key)
            else:
                throw(key, nextvalue)
                return insert_key(key, *values)
        self.assertEqual(['c', 'b', 'a'], insert_key('x', 'a', 'b', 'c'))

    def test_catchall(self):
        def return_all(key):
            return catchall(key)
        def insert_key(key, nextvalue=None, *values):
            if nextvalue is None:
                return return_all(key)
            else:
                throw(key, nextvalue)
                return insert_key(key, *values)
        self.assertEqual(('c', 'b', 'a'), insert_key('x', 'a', 'b', 'c'))

    def test_catcher(self):
        @catcher('x', y='y_val')
        def get(x, y):
            return (x, y)
        throw('x', 'hello')
        throw('y_val', 'world')
        self.assertEqual(('hello', 'world'), get())

