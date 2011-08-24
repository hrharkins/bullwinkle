'''
bullwinkle -- A Python implementation of some of the best Perl::Moose features

Provides numerous capabilities that originally stemmed from Perl::Moose but
may expand outside of that realm over time.  Among these feeatures are:

 * Superclass method override decorators
 * Simplified type-safe proprety declaration
 * Type-safe __init__ keyword arguments via property attributes

In addition, bullwinkle provides:

 * Automatic class member binding via __bindclass__ methods.

'''

from __version__ import *
from bwobject import BWObject
from bwmethod import (before_super, after_super, follow_super, filter_super,
                      override_super, around_super, override_result)
from bwcached import cached, classcached, cachedmethod
from bwmember import member, into
from bwcontext import BWContext
from bwthrowable import throw, catch, BWThrowable, TC

__doc__ += '\nCHANGELOG:\n\n' + str(CHANGELOG)

