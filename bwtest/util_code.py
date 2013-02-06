
import unittest
from bw.util.code import CodeBlock

class TestCodeBlock(unittest.TestCase):
    def test_simple(self):
        result = []
        cb = CodeBlock('fn("Hello")')
        cb.run(fn=result.append)
        self.assertEqual(['Hello'], result)

    def test_extract(self):
        cb = CodeBlock('x = "Hello " + y')
        self.assertEqual('Hello world', cb.extract('x', y='world'))

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
        self.assertEqual(10, cb.result.f(5))

    def test_basic_variable_management(self):
        cb = CodeBlock()
        cb['hello'] = 'world'
        self.assertEqual('world', cb['hello'])
        del cb['hello']
        self.assertIsNone(cb.get('hello'))
        self.assertRaises(KeyError, lambda: cb['hello'])

    def test_anon_variables(self):
        cb = CodeBlock('def f():')
        cb.add('return("Hello %%s" %% %s)' % cb.anon('world'))
        self.assertEqual('Hello world', cb.result.f())
        self.assertTrue('who' in cb.anon('who', 'world'))
        self.assertRaises(TypeError, lambda: cb.anon('a', 'b', 'c'))
        self.assertRaises(TypeError, lambda: cb.anon())

    def test_construction(self):
        cb = CodeBlock('def f(who):')
        with cb.add() as blk:
            cb.add('print("Hello")')
            with cb.add('if %s == test:', 'who', test='world') as blk:
                blk.add('print %s + %s', 'who', 'punc', punc='!')
        self.assertEqual(str(cb).split('\n'),
            [
                'def f(who):',
                '    print("Hello")',
                '    if who == test:',
                '        print who + punc',
            ])

