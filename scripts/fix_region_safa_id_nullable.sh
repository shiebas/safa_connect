#!/bin/bash
# Make safa_id nullable in Region model and apply migration

echo "Making migrations for geography app..."
docker-compose exec web python manage.py makemigrations geography

echo "Applying migrations..."
docker-compose exec web python manage.py migrate geography

echo "Done. The safa_id field in Region should now allow NULLs."