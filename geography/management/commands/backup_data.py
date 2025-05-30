from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
import os

class Command(BaseCommand):
    help = 'Backup existing data from all apps to JSON fixtures'

    def handle(self, *args, **options):
        # Define apps and their models to backup
        apps_to_backup = [
            ('contenttypes', 'contenttypes'),
            ('admin', 'admin'),
            ('auth', 'auth'),
            ('accounts', 'accounts'),
            ('geography', 'geography'),
            ('membership', 'membership')
        ]
        
        os.makedirs('fixtures', exist_ok=True)
        
        # Get list of existing tables
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                AND name NOT LIKE 'django_migrations'
            """)
            existing_tables = {row[0] for row in cursor.fetchall()}

        self.stdout.write("Starting backup process...")
        
        for app, name in apps_to_backup:
            filename = f'fixtures/{name}_data.json'
            self.stdout.write(f"\nBacking up {app} to {filename}")
            
            try:
                call_command(
                    'dumpdata',
                    app,
                    indent=2,
                    output=filename,
                    exclude=['contenttypes.contenttype', 'auth.permission'],
                    natural_foreign=True,
                    verbosity=2
                )
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Successfully backed up {app}")
                )
            except Exception as e:
                self.stderr.write(
                    self.style.WARNING(f"⚠ Skipping {app}: {str(e)}")
                )