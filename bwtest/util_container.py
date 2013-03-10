
import unittest
from bw.util.container import ChainedDict, CachedChainedDict

class ChainedDictTests(unittest.TestCase):
    def test_single(self):
        cd = ChainedDict(x=5, y=7)
        self.assertEqual(5, cd['x'])
        self.assertEqual(7, cd['y'])

    def test_lineage(self):
        root = ChainedDict(x='root_x', y='root_y', z='root_z')
        sub1 = ChainedDict(root, y='sub1_y')
        sub2 = ChainedDict(sub1, x='sub2_x')

        self.assertEqual('sub2_x', sub2['x'])
        self.assertEqual('sub1_y', sub2['y'])
        self.assertEqual('root_z', sub2['z'])

        self.assertIsNone(sub2.get('a'))
        self.assertRaises(KeyError, lambda: sub2['a'])

    def test_shared_base(self):
        root = ChainedDict(x='root_x', y='root_y', z='root_z')
        sub1 = ChainedDict(root, y='sub1_y')
        sub2 = ChainedDict(root, x='sub2_x', a='sub2_a')
        cd = ChainedDict(sub1, sub2)

        self.assertEqual('sub2_x', sub2['x'])
        self.assertEqual('root_y', sub2['y'])
        self.assertEqual('root_z', sub2['z'])
        self.assertEqual('sub2_a', sub2['a'])

    def test_raw_dicts(self):
        d1 = dict(x='d1_x')
        d2 = dict(y='d2_y')
        cd = ChainedDict(d1, d2)

        self.assertEqual('d1_x', cd['x'])
        self.assertEqual('d2_y', cd['y'])

    def test_doubled_bases(self):
        d1 = dict(x='d1_x')
        d2 = dict(y='d2_y')
        cd = ChainedDict(d1, d2, d1)

        self.assertEqual('d1_x', cd['x'])
        self.assertEqual('d2_y', cd['y'])

        root = ChainedDict(x='root_x', y='root_y', z='root_z')
        sub1 = ChainedDict(root, y='sub1_y')
        sub2 = ChainedDict(root, x='sub2_x', a='sub2_a')
        cd = ChainedDict(sub1, sub2, root)

        self.assertEqual('sub2_x', sub2['x'])
        self.assertEqual('root_y', sub2['y'])
        self.assertEqual('root_z', sub2['z'])
        self.assertEqual('sub2_a', sub2['a'])

class FunctionBaseTests(unittest.TestCase):
    def test_simple(self):
        d = dict(x='x')

        @ChainedDict.function
        def getter(k):
            return d.get(k)

        cd = ChainedDict(getter, { 'y': 'y' })
        self.assertEqual('x', cd['x'])
        self.assertEqual('y', cd.get('y'))

    def test_auto_default(self):
        d = dict(x='x')

        @ChainedDict.function(default=False)
        def getter(k):
            return d.get(k)

        cd = ChainedDict(getter, { 'y': 'y' })
        self.assertEqual('x', cd['x'])
        self.assertIsNone(cd.get('y'))

    def test_want_default(self):
        d = dict(x='x')

        @ChainedDict.function(default=True)
        def getter(k, default):
            return d.get(k, default)

        cd = ChainedDict(getter, { 'y': 'y' })
        self.assertEqual('x', cd['x'])
        self.assertEqual('y', cd.get('y'))

    def test_top(self):
        @ChainedDict.function(wants_top=True)
        def adder(top, key):
            if not key.startswith('_'):
                v = top.get('_' + key)
                if v is not None:
                    return v + 1
                else:
                    return v

        cd = ChainedDict(adder, _y = 5)
        self.assertEqual(6, cd['y'])
        self.assertIsNone(cd.get('z'))

        @ChainedDict.function(wants_top=True, default=False)
        def adder(top, key):
            return top['_' + key] + 1

        cd = ChainedDict(adder, _y = 5)
        self.assertEqual(6, cd['y'])

    def test_type_error(self):
        def fails():
            @ChainedDict.function(default='blah')
            def no(): pass
        self.assertRaises(TypeError, fails)

class CachedTests(unittest.TestCase):
    def test_cached_get(self):
        d = dict(x=5)
        cd = CachedChainedDict(d)
        self.assertIsNone(cd.__cache__.get('x'))
        self.assertEqual(5, cd['x'])
        self.assertEqual(5, cd['x'])
        self.assertEqual(5, cd.__cache__.get('x'))

    def test_cache_miss(self):
        d = dict(x=5)
        cd = CachedChainedDict(d)
        self.assertIsNone(cd.get('y'))

