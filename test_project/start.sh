#!/bin/bash

pip install -r ../requirements/dev.txt
pip install django

python ../manage.py migrate

# Set up an admin user, and a sample query
python ../manage.py shell <<ORM
from django.contrib.auth.models import User
u = User.objects.filter(username='admin').first()
if not u:
    u = User(username='admin')
    u.set_password('admin')
    u.is_superuser = True
    u.is_staff = True
    u.save()

from explorer.models import Query
queries = Query.objects.all().count()
if queries == 0:
    q = Query(sql='select * from explorer_query;', title='Sample Query')
    q.save()
ORM

# Flag to indicate whether to proceed with NPM commands
proceed_with_npm=true

# Check if nvm is installed
if command -v nvm >/dev/null 2>&1; then
    nvm install
    nvm use
else
    # Check Node version if nvm is not installed
    current_node_version=$(node -v | cut -d. -f1 | sed 's/v//')
    required_node_version=18
    if [ "$current_node_version" -lt "$required_node_version" ]; then
        echo "Node version is less than 18.0 and nvm is not installed. Please install nvm or upgrade node and re-run."
        proceed_with_npm=false
    fi
fi

if [ "$proceed_with_npm" = true ] ; then
    npm install
    # Start Django server in the background and get its PID
    python ../manage.py runserver 0:8000 &
    DJANGO_PID=$!

    # Set a trap to kill the Django server when the script exits
    trap "echo 'Stopping Django server'; kill $DJANGO_PID" EXIT INT

    # Start Vite dev server
    npm run dev
fi
