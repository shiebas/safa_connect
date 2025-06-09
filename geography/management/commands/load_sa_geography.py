from django.core.management.base import BaseCommand
from geography.models import Province, Region, LocalFootballAssociation
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
        provinces_data = [
            {'name': 'Gauteng', 'code': 'GP', 'capital': 'Johannesburg'},
            {'name': 'KwaZulu-Natal', 'code': 'KZN', 'capital': 'Pietermaritzburg'},
            {'name': 'Western Cape', 'code': 'WC', 'capital': 'Cape Town'},
            {'name': 'Eastern Cape', 'code': 'EC', 'capital': 'Bhisho'},
            {'name': 'Free State', 'code': 'FS', 'capital': 'Bloemfontein'},
            {'name': 'Limpopo', 'code': 'LP', 'capital': 'Polokwane'},
            {'name': 'Mpumalanga', 'code': 'MP', 'capital': 'Mbombela'},
            {'name': 'Northern Cape', 'code': 'NC', 'capital': 'Kimberley'},
            {'name': 'North West', 'code': 'NW', 'capital': 'Mahikeng'},
        ]
        
        for province_data in provinces_data:
            province, created = Province.objects.get_or_create(
                code=province_data['code'],
                defaults={
                    'name': province_data['name'],
                    'capital_city': province_data['capital']
                }
            )
            if created:
                self.stdout.write(f'Created province: {province.name}')
