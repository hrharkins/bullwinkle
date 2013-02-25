#!/bin/bash
#
#   Examples:
#
#   ./run_on_change ./script/coverage.sh
#

CHECK=/tmp/check
rm -f "$CHECK"
while true;
do
    echo "[KKCHEKING..."
    echo -n "[A"
    if [ ! -f "$CHECK" -o "$( find . -newer "$CHECK" )" ];
    then
        eval "clear; clear; $@; echo -n '--- RUN AT: '; date"
        touch "$CHECK"
    else
        echo -n "NO CHANGES FOUND: "; date
        echo -n "[A"
    fi
    sleep 2
done
