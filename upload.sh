#!/bin/bash

cd "$(readlink -f $(dirname $0))"
./coverage.sh
if coverage report | grep -q "TOTAL.*100%$"
then
    git commit -a &&
    git push &&
    python setup.py register &&
    python setup.py sdist upload
else
    echo >&2 'Incomplete code coverage'
    exit 1
fi

