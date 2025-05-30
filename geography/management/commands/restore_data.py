from django.core.management.base import BaseCommand
from django.core.management import call_command
import os

class Command(BaseCommand):
    help = 'Restore data from JSON fixtures'

    def handle(self, *args, **options):
        # Define fixture order based on dependencies
        fixtures_to_restore = [
            'contenttypes_data.json',
            'auth_data.json',
            'accounts_data.json',
            'geography_data.json',
            'membership_data.json'
        ]

        self.stdout.write("Starting restore process...")

        for fixture in fixtures_to_restore:
            fixture_path = f'fixtures/{fixture}'
            
            if not os.path.exists(fixture_path):
                self.stdout.write(
                    self.style.WARNING(f"⚠ Skipping {fixture}: File not found")
                )
                continue

            self.stdout.write(f"\nRestoring from {fixture}")
            
            try:
                call_command(
                    'loaddata',
                    fixture_path,
                    verbosity=2
                )
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Successfully restored {fixture}")
                )
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"✗ Error restoring {fixture}: {str(e)}")
                )

        self.stdout.write(self.style.SUCCESS("\nRestore process completed!"))