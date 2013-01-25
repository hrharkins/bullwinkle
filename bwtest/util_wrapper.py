import unittest
from bw.util.wrapper import *

class TestWrapper(unittest.TestCase):
    def test_simple(self):
        @wrapper
        def simple(fn):
            fn.__here__ = True

        @simple
        def f1(): pass

        self.assertEqual(True, f1.__here__)

