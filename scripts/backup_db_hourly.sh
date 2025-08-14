#!/bin/bash
# Hourly backup script for safa_connect PostgreSQL database
# Place this in scripts/ and add to crontab for hourly execution

BACKUP_DIR="/home/shaun/safa_connect/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="$BACKUP_DIR/safa_db_$TIMESTAMP.sql"

mkdir -p "$BACKUP_DIR"
docker-compose exec db pg_dump -U neetiesister safa_db > "$FILENAME"

# Optional: Remove backups older than 7 daysind "$BACKUP_DIR" -type f -name "safa_db_*.sql" -mtime +7 -delete

echo "Backup completed: $FILENAME"
