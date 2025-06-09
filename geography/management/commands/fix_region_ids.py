from django.core.management.base import BaseCommand
from django.db import transaction
from geography.models import Province, Region, LocalFootballAssociation

class Command(BaseCommand):
    help = 'Fix Eastern Cape region IDs to be sequential 1-8'
    
    def handle(self, *args, **options):
        self.stdout.write('🔧 Fixing Eastern Cape region IDs to 1-8...')
        
        # Expected region order (alphabetical)
        expected_regions = [
            'Alfred Nzo',      # Should be ID 1
            'Amathole',        # Should be ID 2  
            'Buffalo City',    # Should be ID 3
            'Chris Hani',      # Should be ID 4
            'Joe Gqabi',       # Should be ID 5
            'Nelson Mandela Bay', # Should be ID 6
            'OR Tambo',        # Should be ID 7
            'Sarah Baartman'   # Should be ID 8
        ]
        
        try:
            with transaction.atomic():
                province = Province.objects.get(name='Eastern Cape')
                
                # Show current region IDs
                current_regions = Region.objects.filter(province=province).order_by('name')
                self.stdout.write(f'\n📊 Current region IDs:')
                for region in current_regions:
                    self.stdout.write(f'   ID {region.id}: {region.name}')
                
                # Store region data with their LFAs before deletion
                region_data = {}
                for i, region_name in enumerate(expected_regions, 1):
                    try:
                        region = Region.objects.get(name=region_name, province=province)
                        # Save LFA names for this region
                        lfa_names = list(region.localfootballassociation_set.values_list('name', flat=True))
                        region_data[region_name] = lfa_names
                        self.stdout.write(f'   Stored {len(lfa_names)} LFAs for {region_name}')
                    except Region.DoesNotExist:
                        self.stdout.write(f'❌ Missing region: {region_name}')
                
                # Delete all Eastern Cape regions (this will cascade to LFAs)
                self.stdout.write('\n🗑️  Deleting current regions...')
                deleted_count = Region.objects.filter(province=province).delete()
                self.stdout.write(f'   Deleted: {deleted_count}')
                
                # Recreate regions with correct IDs
                self.stdout.write('\n🔧 Recreating regions with correct IDs...')
                for i, region_name in enumerate(expected_regions, 1):
                    # Create region with specific ID
                    region = Region(
                        id=i,
                        name=region_name,
                        province=province
                    )
                    region.save()
                    self.stdout.write(f'   ✅ Created ID {i}: {region_name}')
                    
                    # Recreate LFAs for this region
                    if region_name in region_data:
                        for lfa_name in region_data[region_name]:
                            LocalFootballAssociation.objects.create(
                                name=lfa_name,
                                region=region
                            )
                        self.stdout.write(f'     Restored {len(region_data[region_name])} LFAs')
                
                # Verify the fix
                self.stdout.write(f'\n✅ Final Eastern Cape regions (ID 1-8):')
                fixed_regions = Region.objects.filter(province=province).order_by('id')
                total_lfas = 0
                for region in fixed_regions:
                    lfas_count = region.localfootballassociation_set.count()
                    total_lfas += lfas_count
                    self.stdout.write(f'   ID {region.id}: {region.name} ({lfas_count} LFAs)')
                
                self.stdout.write(
                    self.style.SUCCESS(f'\n🎉 Region IDs fixed successfully! Total LFAs: {total_lfas}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error fixing region IDs: {str(e)}')
            )
