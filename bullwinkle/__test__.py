'''
__test__ -- provides testing for bullwinkle

This can be invoked via python -m bullwinkle.__test__
'''

import doctest

if __name__ == '__main__':
    import bwobject, bwmethod, bwcached, bwmember
    doctest.testmod(bwobject)
    doctest.testmod(bwmethod)
    doctest.testmod(bwcached)
    doctest.testmod(bwmember)

