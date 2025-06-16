#!/bin/bash
# Script to drop the unique constraint on safa_id in geography_region

echo "Dropping unique constraint on safa_id in geography_region..."
docker-compose exec db psql -U neetiesister safa_db -c 'ALTER TABLE geography_region DROP CONSTRAINT IF EXISTS geography_region_safa_id_key;'
echo "Constraint dropped. You can now load your fixture without unique safa_id errors."
