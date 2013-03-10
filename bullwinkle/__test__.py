'''
__test__ -- provides testing for bullwinkle

This can be invoked via python bullwinkle.__test__
'''

import doctest

if __name__ == '__main__':
    import sys, os

    # Make sure the bullwinkle library is in the path.
    bwdir = os.path.dirname(os.path.realpath(sys.argv[0]))
    sys.path.insert(0, os.path.dirname(bwdir))

    import bwversion, bwobject, bwmethod, bwcontext, bwcoder
    import bwcached, bwmember, bwthrowable#, bwconvertable
    doctest.testmod(bwversion)
    doctest.testmod(bwobject)
    doctest.testmod(bwmethod)
    doctest.testmod(bwcontext)
    doctest.testmod(bwcoder)
    doctest.testmod(bwcached)
    doctest.testmod(bwmember)
    doctest.testmod(bwthrowable)
    #doctest.testmod(bwconvertable)

