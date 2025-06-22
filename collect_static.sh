#!/bin/bash

# Script to collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Static files collected successfully."
