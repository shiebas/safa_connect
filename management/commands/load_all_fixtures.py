from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Load all core fixtures for SAFA Connect system in the correct order.'

    def handle(self, *args, **options):
        fixture_list = [
            'geography/fixtures/geography_worldsportsbody.json',
            'geography/fixtures/geography_continent.json',
            'geography/fixtures/geography_continentfederation.json',
            'geography/fixtures/geography_continentregion.json',
            'geography/fixtures/geography_country.json',
            'geography/fixtures/geography_motherbody.json',
            # Add more fixture paths as needed
        ]
        for fixture in fixture_list:
            self.stdout.write(self.style.NOTICE(f'Loading {fixture}...'))
            call_command('loaddata', fixture)
        self.stdout.write(self.style.SUCCESS('All core fixtures loaded successfully!'))
