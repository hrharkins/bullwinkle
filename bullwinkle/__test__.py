'''
__test__ -- provides testing for bullwinkle

This can be invoked via python bullwinkle.__test__
'''

import doctest

if __name__ == '__main__':
    import __changelog__, bwobject, bwmethod
    import bwcached, bwmember, bwthrowable
    doctest.testmod(__changelog__)
    doctest.testmod(bwobject)
    doctest.testmod(bwmethod)
    doctest.testmod(bwcached)
    doctest.testmod(bwmember)
    doctest.testmod(bwthrowable)

