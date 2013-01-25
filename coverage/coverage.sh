#!/bin/bash
#
#   Requires http://pypi.python.org/pypi/coverage version 3.6
#   (easy_install coverage)
#
#   See also: .coveragerc
#

export PYTHONPATH=$PWD
rm -f coverage/unittest.coverage coverage/doctest.coverage
coverage run --rcfile=coverage/unittest.conf -m unittest bwtest
coverage run --rcfile=coverage/doctest.conf -m doctest bw/*.py bw/*/*.py
coverage html --rcfile=coverage/unittest.conf -d coverage/results/unittest
coverage html --rcfile=coverage/doctest.conf -d coverage/results/doctest

# Check for Total = 100%, dump on failure
for type in unittest doctest
do
    if ! coverage report --rcfile=coverage/$type.conf |
         grep -q '^TOTAL.*100%$';
    then
        coverage report -m --rcfile=coverage/$type.conf
        exit
    fi
done