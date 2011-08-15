'''
__test__ -- provides testing for bullwinkle

This can be invoked via python bullwinkle.__test__
'''

import doctest

if __name__ == '__main__':
    import bwversion, bwobject, bwmethod, bwcontext
    import bwcached, bwmember, bwthrowable
    doctest.testmod(bwversion)
    doctest.testmod(bwobject)
    doctest.testmod(bwmethod)
    doctest.testmod(bwcontext)
    doctest.testmod(bwcached)
    doctest.testmod(bwmember)
    doctest.testmod(bwthrowable)

