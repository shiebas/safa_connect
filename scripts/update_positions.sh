#!/bin/bash

# Script to update position data in a safer way using direct SQL

# Create a backup file
BACKUP_FILE="positions_backup_$(date +%Y%m%d_%H%M%S).sql"
echo "Creating backup to $BACKUP_FILE..."
echo ".headers on\n.mode insert\nSELECT * FROM accounts_position;" | python manage.py dbshell > "$BACKUP_FILE"

# Update positions table
echo "Updating positions table..."
python manage.py shell << EOF
from django.db import connection
from accounts.models import Position

# Get all positions
positions = Position.objects.all()
print(f"Found {len(positions)} positions")

# First make titles unique
title_counts = {}
for pos in positions:
    if pos.title in title_counts:
        title_counts[pos.title] += 1
        pos.title = f"{pos.title} ({pos.level})"
        pos.save()
        print(f"Updated duplicate title to: {pos.title}")
    else:
        title_counts[pos.title] = 1

# Now add a levels column and populate it
with connection.cursor() as cursor:
    # Check if the column exists
    cursor.execute("PRAGMA table_info(accounts_position)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'levels' not in columns:
        print("Adding levels column...")
        cursor.execute("ALTER TABLE accounts_position ADD COLUMN levels VARCHAR(100) DEFAULT 'NATIONAL,PROVINCE,REGION,LFA,CLUB'")

# Update the levels field for each position based on level
for pos in Position.objects.all():
    if not pos.levels:
        pos.levels = pos.level
        pos.save()
        print(f"Set levels={pos.level} for position {pos.title}")

print("Position changes completed successfully!")
EOF

echo "Done! Check the backup file if you need to restore."
