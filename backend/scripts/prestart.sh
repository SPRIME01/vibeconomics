#! /usr/bin/env bash

set -e
set -x

# Let the DB start
# The WORKDIR in the Docker image is /app/src/
python app/backend_pre_start.py

# Run migrations
# Alembic should be run from the project root where alembic.ini is located.
# The Dockerfile copies alembic.ini to /app/
(cd /app && alembic upgrade head)

# Create initial data in DB
# This script is also in app/
python app/initial_data.py
