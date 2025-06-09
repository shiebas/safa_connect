from django.core.management.base import BaseCommand
from django.db import transaction
from geography.models import Province, Region, LocalFootballAssociation

class Command(BaseCommand):
    help = 'Delete all LFAs for Eastern Cape regions'
    
    def handle(self, *args, **options):
        try:
            province = Province.objects.get(name='Eastern Cape')
            regions = province.region_set.all().order_by('id')
            
            self.stdout.write('🗑️  Deleting all Eastern Cape LFAs...')
            
            total_deleted = 0
            for region in regions:
                lfa_count = region.localfootballassociation_set.count()
                if lfa_count > 0:
                    region.localfootballassociation_set.all().delete()
                    self.stdout.write(f'   Region {region.id} ({region.name}): Deleted {lfa_count} LFAs')
                    total_deleted += lfa_count
                else:
                    self.stdout.write(f'   Region {region.id} ({region.name}): No LFAs to delete')
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Deleted {total_deleted} LFAs from Eastern Cape')
            )
            
            # Show clean regions
            self.stdout.write('\n📋 Eastern Cape regions (now empty):')
            for region in regions:
                self.stdout.write(f'   Region {region.id}: {region.name} (0 LFAs)')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
