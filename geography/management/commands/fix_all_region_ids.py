from django.core.management.base import BaseCommand
from django.db import transaction
from geography.models import Province, Region, LocalFootballAssociation

class Command(BaseCommand):
    help = 'Fix ALL region IDs to be sequential 1-52'
    
    def handle(self, *args, **options):
        self.stdout.write('🔧 Fixing ALL region IDs to be sequential...')
        
        # Define the complete structure with correct ID ranges
        province_structure = {
            'Eastern Cape': {'start_id': 1, 'regions': [
                'Alfred Nzo', 'Amathole', 'Buffalo City', 'Chris Hani',
                'Joe Gqabi', 'Nelson Mandela Bay', 'OR Tambo', 'Sarah Baartman'
            ]},
            'Free State': {'start_id': 9, 'regions': [
                'Fezile Dabi', 'Lejweleputswa', 'Mangaung', 'Thabo Mofutsanyana', 'Xhariep'
            ]},
            'Gauteng': {'start_id': 14, 'regions': [
                'Ekurhuleni', 'Johannesburg', 'Sedibeng', 'Tshwane', 'West Rand'
            ]},
            'KwaZulu-Natal': {'start_id': 19, 'regions': [
                # Add KZN regions here when ready
            ]},
            # Add other provinces as needed
        }
        
        try:
            with transaction.atomic():
                # Store all LFA data before making changes
                lfa_data = {}
                for region in Region.objects.all():
                    lfa_names = list(region.localfootballassociation_set.values_list('name', flat=True))
                    lfa_data[f"{region.province.name}_{region.name}"] = lfa_names
                
                # Delete all regions (LFAs will cascade)
                Region.objects.all().delete()
                self.stdout.write('🗑️  Deleted all existing regions')
                
                # Recreate regions with correct IDs
                for province_name, config in province_structure.items():
                    try:
                        province = Province.objects.get(name=province_name)
                        region_id = config['start_id']
                        
                        self.stdout.write(f'\n🏛️  {province_name}:')
                        
                        for region_name in config['regions']:
                            # Create region with correct ID
                            region = Region(
                                id=region_id,
                                name=region_name,
                                province=province
                            )
                            region.save()
                            self.stdout.write(f'   ✅ ID {region_id}: {region_name}')
                            
                            # Restore LFAs
                            key = f"{province_name}_{region_name}"
                            if key in lfa_data:
                                for lfa_name in lfa_data[key]:
                                    LocalFootballAssociation.objects.create(
                                        name=lfa_name,
                                        region=region
                                    )
                                self.stdout.write(f'     Restored {len(lfa_data[key])} LFAs')
                            
                            region_id += 1
                    
                    except Province.DoesNotExist:
                        self.stdout.write(f'❌ Province not found: {province_name}')
                
                # Final verification
                self.stdout.write('\n📊 Final structure:')
                for province in Province.objects.all().order_by('id'):
                    regions = province.region_set.all().order_by('id')
                    if regions.exists():
                        total_lfas = LocalFootballAssociation.objects.filter(region__province=province).count()
                        self.stdout.write(f'  {province.name}: {regions.count()} regions, {total_lfas} LFAs')
                        for region in regions:
                            lfas = region.localfootballassociation_set.count()
                            self.stdout.write(f'    ID {region.id}: {region.name} ({lfas} LFAs)')
                
                self.stdout.write(self.style.SUCCESS('\n✅ All region IDs fixed!'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
