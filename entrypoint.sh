#!/bin/sh
# entrypoint.sh
# Entrypoint for Django container: wait for Postgres, migrate, collectstatic, then run server

set -e

# Wait for Postgres to be ready
/code/wait-for-postgres.sh db

# Apply database migrations
python manage.py migrate --noinput

# Collect static files (optional, safe to run always)
python manage.py collectstatic --noinput

# Start Django server
exec python manage.py runserver 0.0.0.0:8000
