#!/bin/sh
# wait-for-postgres.sh
# Wait until Postgres is ready before starting Django

set -e

host="$1"
shift

MAX_TRIES=60
TRIES=0

until pg_isready -h "$host" -p "5432"; do
  >&2 echo "Postgres is unavailable - sleeping ($TRIES)"
  sleep 1
  TRIES=$((TRIES+1))
  if [ $TRIES -ge $MAX_TRIES ]; then
    >&2 echo "Error: Postgres did not become available after $MAX_TRIES seconds. Exiting."
    exit 1
  fi
done

>&2 echo "Postgres is up - executing command"
exec "$@"
