from django.core.management.base import BaseCommand
from geography.models import Province, Region, LocalFootballAssociation

class Command(BaseCommand):
    help = 'List Eastern Cape regions (ID 1-8) with their LFAs'
    
    def handle(self, *args, **options):
        self.stdout.write('📋 Eastern Cape Regions and LFAs:')
        
        try:
            province = Province.objects.get(name='Eastern Cape')
            regions = province.region_set.all().order_by('id')
            
            self.stdout.write(f'\n🏛️  {province.name} (Province ID: {province.id})')
            self.stdout.write(f'   Total Regions: {regions.count()}')
            
            for region in regions:
                lfas = region.localfootballassociation_set.all().order_by('name')
                self.stdout.write(f'\n📍 Region ID {region.id}: {region.name}')
                self.stdout.write(f'   LFAs ({lfas.count()}):')
                
                for i, lfa in enumerate(lfas, 1):
                    self.stdout.write(f'     {i:2d}. {lfa.name}')
            
            # Summary
            total_lfas = LocalFootballAssociation.objects.filter(region__province=province).count()
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n📊 Summary:\n'
                    f'   Regions: {regions.count()}/8\n'
                    f'   Total LFAs: {total_lfas}/56'
                )
            )
            
        except Province.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Eastern Cape province not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
