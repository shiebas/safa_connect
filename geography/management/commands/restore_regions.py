from django.core.management.base import BaseCommand
from django.db import transaction
from geography.models import Province, Region, LocalFootballAssociation

class Command(BaseCommand):
    help = 'Restore all regions with correct province relationships'
    
    def handle(self, *args, **options):
        self.stdout.write('🔧 Restoring regions for all provinces...')
        
        # Eastern Cape - 8 Regions with 56 LFAs (in alphabetical order)
        regions_by_province = {
            'Eastern Cape': {
                'Alfred Nzo': [
                    'Mount Ayliff LFA', 'Mount Frere LFA', 'Matatiele LFA',
                    'Cedarville LFA', 'Kokstad LFA', 'Umzimkulu LFA',
                    'Maluti LFA', 'Ntabankulu LFA'
                ],
                'Amathole': [
                    'Cathcart LFA', 'Stutterheim LFA', 'Fort Beaufort LFA',
                    'Adelaide LFA', 'Bedford LFA', 'Hogsback LFA',
                    'Alice LFA', 'Keiskammahoek LFA'
                ],
                'Buffalo City': [
                    'East London LFA', 'Mdantsane LFA', 'Duncan Village LFA', 
                    'Scenery Park LFA', 'King Williams Town LFA', 'Zwelitsha LFA',
                    'Bhisho LFA'
                ],
                'Chris Hani': [
                    'Queenstown LFA', 'Cofimvaba LFA', 'Cradock LFA',
                    'Middelburg LFA', 'Steynsburg LFA', 'Burgersdorp LFA',
                    'Tarkastad LFA'
                ],
                'Joe Gqabi': [
                    'Aliwal North LFA', 'Barkly East LFA', 'Lady Grey LFA',
                    'Ugie LFA', 'Maclear LFA', 'Rhodes LFA',
                    'Sterkspruit LFA'
                ],
                'Nelson Mandela Bay': [
                    'Port Elizabeth LFA', 'New Brighton LFA', 'KwaNobuhle LFA', 
                    'Motherwell LFA', 'Uitenhage LFA', 'Despatch LFA',
                    'Bethelsdorp LFA', 'Gelvandale LFA'
                ],
                'OR Tambo': [
                    'Mthatha LFA', 'Mqanduli LFA', 'Ngcobo LFA',
                    'Libode LFA', 'Lusikisiki LFA', 'Port St Johns LFA',
                    'Flagstaff LFA', 'Bizana LFA'
                ],
                'Sarah Baartman': [
                    'Graaff-Reinet LFA', 'Somerset East LFA', 'Pearston LFA',
                    'Jansenville LFA', 'Willowmore LFA', 'Steytlerville LFA',
                    'Kirkwood LFA'
                ]
            }
        }

        try:
            with transaction.atomic():
                # Focus on Eastern Cape first
                province_name = 'Eastern Cape'
                
                try:
                    province = Province.objects.get(name=province_name)
                    self.stdout.write(f'\n🏛️  {province_name} (ID: {province.id})')
                    
                    total_regions = 0
                    total_lfas = 0
                    
                    for region_name, lfa_names in regions_by_province[province_name].items():
                        # Create region
                        region, created = Region.objects.get_or_create(
                            name=region_name,
                            province=province
                        )
                        
                        if created:
                            total_regions += 1
                            self.stdout.write(f'   ✅ Created region: {region_name}')
                        else:
                            self.stdout.write(f'   🔄 Region exists: {region_name}')
                        
                        # Create LFAs for this region
                        region_lfas = 0
                        for lfa_name in lfa_names:
                            lfa, lfa_created = LocalFootballAssociation.objects.get_or_create(
                                name=lfa_name,
                                region=region
                            )
                            
                            if lfa_created:
                                region_lfas += 1
                                total_lfas += 1
                                self.stdout.write(f'     ✅ Created LFA: {lfa_name}')
                        
                        self.stdout.write(f'     📊 {region_lfas} LFAs in {region_name}')
                    
                    # Verify Eastern Cape totals
                    final_regions = province.region_set.count()
                    final_lfas = LocalFootballAssociation.objects.filter(region__province=province).count()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'\n🎉 Eastern Cape restored!\n'
                            f'   ✅ {final_regions} Regions (target: 8)\n'
                            f'   ✅ {final_lfas} LFAs (target: 56)\n'
                            f'   📊 Created {total_regions} regions, {total_lfas} LFAs this run'
                        )
                    )
                    
                    if final_regions == 8 and final_lfas == 56:
                        self.stdout.write(self.style.SUCCESS('✅ Eastern Cape structure matches target!'))
                    else:
                        self.stdout.write(self.style.WARNING(f'⚠️  Structure mismatch - check data'))
                    
                except Province.DoesNotExist:
                    self.stdout.write(f'   ❌ Province not found: {province_name}')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error restoring Eastern Cape: {str(e)}')
            )
