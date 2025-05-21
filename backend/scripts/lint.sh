#!/usr/bin/env bash

set -e
set -x

mypy src/app
ruff check src/app
ruff format src/app --check
