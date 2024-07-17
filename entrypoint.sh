#!/bin/bash
# entrypoint.sh

set -e

# Source the nvm script to set up the environment
# This should match the version referenced in Dockerfile
. /root/.nvm/nvm.sh
nvm use 20.15.1

# Django
python manage.py migrate
python manage.py runserver 0.0.0.0:8000 &
echo "Django server started"

# Vite dev server
export APP_VERSION=$(python -c 'from explorer import __version__; print(__version__)')
echo "Starting Vite with APP_VERSION=${APP_VERSION}"
npx vite --config vite.config.mjs
