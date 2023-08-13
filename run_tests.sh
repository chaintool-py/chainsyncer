#!/bin/bash

set -e
set -x
path=${PYTHONPATH:-.}
export PYTHONPATH=$path
>&2 echo using pythonpath $PYTHONPATH
for f in `ls tests/*.py`; do
	python $f
	if [ $? -gt 0 ]; then
		exit
	fi
done

for f in `ls tests/store/test_*_*.py`; do
	python $f
	if [ $? -gt 0 ]; then
		exit
	fi
done
set +x
set +e
