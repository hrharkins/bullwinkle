#!/bin/bash
#
#   See also: .coveragerc
#

export PYTHONPATH=$PWD
echo 'import bullwinkle.__license__' >/tmp/x.py
echo 'import bullwinkle.__changelog__' >>/tmp/x.py
echo 'import bullwinkle.__test__' >>/tmp/x.py
coverage run bullwinkle/__test__.py
coverage run -a bullwinkle/__version__.py >/dev/null
coverage run -a bullwinkle/__changelog__.py >/dev/null
coverage run -a bullwinkle/__license__.py >/dev/null
coverage run -a /tmp/x.py
coverage html
