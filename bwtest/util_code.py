
import unittest
from bw.util.code import CodeBlock

class TestCodeBlock(unittest.TestCase):
    def test_simple(self):
        result = []
        cb = CodeBlock('fn("Hello")')
        cb.run(fn=result.append)
        self.assertEqual(['Hello'], result)

    def test_extract(self):
        cb = CodeBlock('x = 5')
        self.assertEqual(5, cb['x'])

    def test_block_member_types(self):
        cb = CodeBlock()
        cb.append('fn("Hello")')
        cb.append(['fn("Doctor")'])
        cb.append(iter(('fn("Name")', 'fn("Continue")')))
        cb.append(lambda cb: 'fn("Yesterday")')
        cb.append(CodeBlock('fn("Tomorrow")'))
        result = []
        cb.run(fn=result.append)
        self.assertEqual(['Hello', 'Doctor',
                          'Name', 'Continue',
                          'Yesterday', 'Tomorrow'], result)

    def test_function_declare(self):
        cb = CodeBlock('def f(x):')
        cb.append('return x * 2')
        self.assertEqual(10, cb['f'](5))

