'''
__test__ -- provides testing for bullwinkle

This can be invoked via python bullwinkle.__test__
'''

import doctest

if __name__ == '__main__':
    import bwobject, bwmethod, bwcached, bwmember, bwthrowable
    doctest.testmod(bwobject)
    doctest.testmod(bwmethod)
    doctest.testmod(bwcached)
    doctest.testmod(bwmember)
    doctest.testmod(bwthrowable)

