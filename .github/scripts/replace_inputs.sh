#!/bin/bash

mytmpdir=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')
export INPUT_FILE="repo_manager/utils/_inputs.py"
export REPLACEMENT=$(python .github/scripts/generate_inputs.py)

NEW_INIT=$(.github/scripts/replace.sed $INPUT_FILE | envsubst)
echo -n "$NEW_INIT" > "$mytmpdir/__init__.py"
black --line-length=119 --target-version=py39 "$mytmpdir/__init__.py"

if diff $INPUT_FILE "$mytmpdir/__init__.py"; then
    echo "Inputs up to date"
else
    echo "Inputs out of date...updating"
    cp "$mytmpdir/__init__.py" $INPUT_FILE
fi

rm -rf $mytmpdir
