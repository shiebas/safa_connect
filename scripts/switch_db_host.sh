#!/bin/bash
# Usage: bash scripts/switch_db_host.sh [docker|local]
# Switches POSTGRES_HOST in .env for Docker Compose or local development

ENV_FILE=".env"

if [ "$1" = "docker" ]; then
    sed -i 's/^POSTGRES_HOST=.*/POSTGRES_HOST=db/' "$ENV_FILE"
    echo "POSTGRES_HOST set to 'db' for Docker Compose."
elif [ "$1" = "local" ]; then
    sed -i 's/^POSTGRES_HOST=.*/POSTGRES_HOST=127.0.0.1/' "$ENV_FILE"
    echo "POSTGRES_HOST set to '127.0.0.1' for local development."
else
    echo "Usage: bash scripts/switch_db_host.sh [docker|local]"
    exit 1
fi
