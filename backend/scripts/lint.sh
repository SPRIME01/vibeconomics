#!/usr/bin/env bash

set -e
set -x

pyre
ruff check src/app
ruff format src/app --check
