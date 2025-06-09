from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
import json

class Command(BaseCommand):
    help = 'Load complete South African geography data with sample LFAs and clubs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Clear existing data before loading',
        )
    
    def handle(self, *args, **options):
        from geography.models import Province, Region, LocalFootballAssociation, Club
        
        # First, show current data status
        current_provinces = Province.objects.count()
        current_regions = Region.objects.count() 
        current_lfas = LocalFootballAssociation.objects.count()
        current_clubs = Club.objects.count()
        
        self.stdout.write(f'📊 Current data:')
        self.stdout.write(f'   - {current_provinces} Provinces')
        self.stdout.write(f'   - {current_regions} Regions') 
        self.stdout.write(f'   - {current_lfas} LFAs')
        self.stdout.write(f'   - {current_clubs} Clubs')
        
        if options['reset']:
            self.stdout.write('🗑️  Clearing existing geography data...')
            Club.objects.all().delete()
            LocalFootballAssociation.objects.all().delete()
            Region.objects.all().delete()
            Province.objects.all().delete()
            self.stdout.write('✅ Existing data cleared')
        elif current_provinces > 0:
            self.stdout.write('ℹ️  Keeping existing data and adding fixtures...')
        
        # Generate fixtures file if it doesn't exist
        fixtures_file = 'geography/fixtures/complete_geography.json'
        if not os.path.exists(fixtures_file):
            self.stdout.write('📝 Generating fixtures file...')
            from geography.fixtures.load_sa_geography import save_fixtures_to_file
            save_fixtures_to_file()
        
        # Load fixtures
        self.stdout.write('📥 Loading complete geography data...')
        try:
            call_command('loaddata', 'complete_geography.json')
            
            # Show summary
            provinces_count = Province.objects.count()
            regions_count = Region.objects.count()
            lfas_count = LocalFootballAssociation.objects.count()
            clubs_count = Club.objects.count()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Successfully loaded complete geography data:\n'
                    f'   - {provinces_count} Provinces\n'
                    f'   - {regions_count} Regions\n'
                    f'   - {lfas_count} LFAs\n'
                    f'   - {clubs_count} Clubs'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error loading fixtures: {str(e)}')
            )
