#!/bin/bash
# Script to fix safa_id constraint and upload region fixture in Docker Compose

set -e

# Step 1: Set all empty safa_id values to NULL

echo "Setting empty safa_id values to NULL..."
docker-compose exec db psql -U neetiesister safa_db -c "UPDATE geography_region SET safa_id = NULL WHERE safa_id = '';"

# Step 2: Drop and recreate the unique constraint (to allow multiple NULLs)
echo "Dropping and recreating unique constraint on safa_id..."
docker-compose exec db psql -U neetiesister safa_db -c "ALTER TABLE geography_region DROP CONSTRAINT IF EXISTS geography_region_safa_id_key;"
docker-compose exec db psql -U neetiesister safa_db -c "ALTER TABLE geography_region ADD CONSTRAINT geography_region_safa_id_key UNIQUE (safa_id);"

# Step 3: Upload the region fixture
echo "Loading region fixture..."
docker-compose exec web python manage.py loaddata geography/fixtures/geography_region.json

echo "Region fixture upload complete!"
