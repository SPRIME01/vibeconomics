#! /usr/bin/env bash
set -e
set -x

python tests/scripts/tests_pre_start.py

bash scripts/test.sh "$@"
