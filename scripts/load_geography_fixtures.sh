#!/bin/bash
# Load all core geography fixtures in the correct order for SAFA Global
# Usage: bash load_geography_fixtures.sh

set -e

# Load World Sports Body (FIFA)
echo "Loading WorldSportsBody..."
docker-compose exec web python manage.py loaddata geography/fixtures/geography_worldsportsbody.json

# Load Continents (Africa, Asia, etc.)
echo "Loading Continents..."
docker-compose exec web python manage.py loaddata geography/fixtures/geography_continent.json

# Load Continent Federation (CAF)
echo "Loading ContinentFederation (CAF)..."
docker-compose exec web python manage.py loaddata geography/fixtures/geography_continentfederation.json

# Load Continent Region (Southern Africa)
echo "Loading ContinentRegion (Southern Africa)..."
docker-compose exec web python manage.py loaddata geography/fixtures/geography_continentregion.json

# Load Countries (South Africa, etc.)
echo "Loading Countries..."
docker-compose exec web python manage.py loaddata geography/fixtures/geography_country.json

# Load MotherBody (SAFAM)
echo "Loading MotherBody (SAFAM)..."
docker-compose exec web python manage.py loaddata geography/fixtures/geography_motherbody.json

echo "All core geography fixtures loaded successfully!"
