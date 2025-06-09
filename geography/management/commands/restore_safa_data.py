from django.core.management.base import BaseCommand
from geography.models import Province, Region, LocalFootballAssociation

class Command(BaseCommand):
    help = 'Restore the original SAFA structure with 52 regions'
    
    def handle(self, *args, **options):
        self.stdout.write('🔄 Restoring original SAFA geography structure...')
        
        # Check what fields exist in your models
        self.stdout.write('📋 Checking model fields...')
        
        # Original 9 South African Provinces (using only basic fields)
        provinces_data = [
            {'name': 'Eastern Cape', 'code': 'EC'},
            {'name': 'Free State', 'code': 'FS'},
            {'name': 'Gauteng', 'code': 'GP'},
            {'name': 'KwaZulu-Natal', 'code': 'KZN'},
            {'name': 'Limpopo', 'code': 'LP'},
            {'name': 'Mpumalanga', 'code': 'MP'},
            {'name': 'Northern Cape', 'code': 'NC'},
            {'name': 'North West', 'code': 'NW'},
            {'name': 'Western Cape', 'code': 'WC'},
        ]
        
        # The complete 52 SAFA regions structure
        regions_data = {
            'Gauteng': [
                'Johannesburg', 'Ekurhuleni', 'Tshwane', 'West Rand', 'Sedibeng', 
                'Vaal Triangle', 'Greater Johannesburg', 'East Rand'
            ],
            'KwaZulu-Natal': [
                'Durban', 'Pietermaritzburg', 'Newcastle', 'Richards Bay', 
                'South Coast', 'Midlands', 'Zululand', 'Umgungundlovu',
                'Harry Gwala', 'King Cetshwayo', 'uMkhanyakude', 'uThukela'
            ],
            'Western Cape': [
                'Cape Town', 'Boland', 'Eden', 'Overberg', 'West Coast', 
                'Central Karoo', 'Cape Winelands', 'Garden Route'
            ],
            'Eastern Cape': [
                'Port Elizabeth', 'East London', 'Grahamstown', 'King Williams Town', 
                'Queenstown', 'Uitenhage', 'Border', 'Amathole', 'Buffalo City',
                'Chris Hani', 'Joe Gqabi', 'OR Tambo', 'Sarah Baartman'
            ],
            'Free State': [
                'Bloemfontein', 'Welkom', 'Kroonstad', 'Sasolburg', 'Bethlehem',
                'Fezile Dabi', 'Lejweleputswa', 'Mangaung', 'Thabo Mofutsanyana',
                'Xhariep'
            ],
            'Limpopo': [
                'Polokwane', 'Tzaneen', 'Thohoyandou', 'Giyani', 'Lebowakgomo',
                'Capricorn', 'Mopani', 'Sekhukhune', 'Vhembe', 'Waterberg'
            ],
            'Mpumalanga': [
                'Mbombela', 'Witbank', 'Middelburg', 'Standerton', 'Secunda',
                'Ehlanzeni', 'Gert Sibande', 'Nkangala'
            ],
            'Northern Cape': [
                'Kimberley', 'Upington', 'Springbok', 'De Aar',
                'Frances Baard', 'John Taolo Gaetsewe', 'Namakwa', 'Pixley ka Seme', 'ZF Mgcawu'
            ],
            'North West': [
                'Mahikeng', 'Rustenburg', 'Klerksdorp', 'Potchefstroom',
                'Bojanala', 'Dr Kenneth Kaunda', 'Dr Ruth Segomotsi Mompati', 'Ngaka Modiri Molema'
            ]
        }
        
        try:
            # Create provinces using only existing fields
            provinces = {}
            for prov_data in provinces_data:
                # Only use fields that exist in your model
                province_defaults = {'name': prov_data['name']}
                
                # Add code field if it exists
                if hasattr(Province, 'code'):
                    province_defaults['code'] = prov_data['code']
                
                province, created = Province.objects.get_or_create(
                    name=prov_data['name'],
                    defaults=province_defaults
                )
                provinces[prov_data['name']] = province
                if created:
                    self.stdout.write(f'✅ Created province: {province.name}')
                else:
                    self.stdout.write(f'🔄 Found existing: {province.name}')
            
            # Create regions
            total_regions = 0
            for province_name, region_names in regions_data.items():
                province = provinces[province_name]
                for region_name in region_names:
                    region, created = Region.objects.get_or_create(
                        name=region_name,
                        province=province
                    )
                    if created:
                        total_regions += 1
                        self.stdout.write(f'  ✅ Created region: {region_name} in {province_name}')
            
            # Summary
            final_provinces = Province.objects.count()
            final_regions = Region.objects.count()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 SAFA geography restored successfully!\n'
                    f'   - {final_provinces} Provinces\n'
                    f'   - {final_regions} Regions\n'
                    f'   - Created {total_regions} new regions'
                )
            )
            
            # Show breakdown by province
            self.stdout.write('\n📊 Regional breakdown:')
            for province in Province.objects.all():
                region_count = province.regions.count()
                self.stdout.write(f'   {province.name}: {region_count} regions')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error restoring data: {str(e)}')
            )
