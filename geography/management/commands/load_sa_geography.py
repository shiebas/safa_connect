from django.core.management.base import BaseCommand
from geography.models import Province, Region, LocalFootballAssociation, NationalFederation, Country
import json
import os

class Command(BaseCommand):
    help = 'Load South African geography data'
    
    def handle(self, *args, **options):
        self.stdout.write('Loading South African geography data...')
        
        # Load provinces
        self.load_provinces()
        
        # Load regions  
        self.load_regions()
        
        # Load sample LFAs
        self.load_sample_lfas()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully loaded geography data')
        )
    
    def load_provinces(self):
        # Ensure South Africa and SAFA exist
        country, country_created = Country.objects.get_or_create(
            name="South Africa",
            defaults={'code': 'ZAF'}
        )
        if country_created:
            self.stdout.write(self.style.SUCCESS('Created Country: South Africa'))

        national_federation, federation_created = NationalFederation.objects.get_or_create(
            name="South African Football Association",
            defaults={'acronym': 'SAFA', 'country': country}
        )
        if federation_created:
            self.stdout.write(self.style.SUCCESS('Created National Federation: SAFA'))

        json_file_path = os.path.join('databackup29072025', 'geography_province.json')

        try:
            with open(json_file_path, 'r') as f:
                provinces_data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {json_file_path}"))
            return
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f"Error decoding JSON from {json_file_path}"))
            return

        for province_data in provinces_data:
            province, created = Province.objects.update_or_create(
                name=province_data['name'],
                defaults={
                    'code': province_data.get('code', ''),
                    'safa_id': province_data.get('safa_id', ''),
                    'description': province_data.get('description', ''),
                    'national_federation': national_federation,
                }
            )
            if created:
                self.stdout.write(f'Created province: {province.name}')
            else:
                self.stdout.write(f'Updated province: {province.name}')

    def load_regions(self):
        self.stdout.write('Skipping region loading.')
        pass

    def load_sample_lfas(self):
        self.stdout.write('Skipping LFA loading.')
        pass
