#!/bin/bash

workdir=$(dirname $(which $0))
cd $workdir

export PYTHONPATH="$workdir/../src"

for i in test_*.py; do
    echo -en "\nTEST: $i\n"
    trial $i
    echo
done
