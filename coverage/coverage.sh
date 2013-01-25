#!/bin/bash
#
#   Requires http://pypi.python.org/pypi/coverage version 3.6
#   (easy_install coverage)
#
#   See also: .coveragerc
#

export PYTHONPATH=$PWD
coverage run --rcfile=coverage/unittest.conf -m unittest bwtest
coverage run --rcfile=coverage/doctest.conf -m doctest bw/*.py bw/*/*.py
coverage html --rcfile=coverage/unittest.conf -d coverage/results/unittest
coverage html --rcfile=coverage/doctest.conf -d coverage/results/doctest

