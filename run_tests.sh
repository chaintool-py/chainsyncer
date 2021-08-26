#!/bin/bash

set -e
set -x
for f in `ls tests/*.py`; do
	python $f
	if [ $? -gt 0 ]; then
		exit
	fi
done
set +x
set +e
