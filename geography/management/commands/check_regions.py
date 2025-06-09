from django.core.management.base import BaseCommand
from django.db import transaction
from geography.models import Province, Region, LocalFootballAssociation

class Command(BaseCommand):
    help = 'Check region relationships and fix if needed'
    
    def handle(self, *args, **options):
        self.stdout.write('🔍 Checking all regions and their IDs...')
        
        # Check all provinces and their regions
        provinces = Province.objects.all().order_by('id')
        
        total_regions = 0
        total_lfas = 0
        
        for province in provinces:
            regions = Region.objects.filter(province=province).order_by('id')
            province_lfas = LocalFootballAssociation.objects.filter(region__province=province).count()
            
            self.stdout.write(f'\n🏛️  Province ID {province.id}: {province.name}')
            self.stdout.write(f'   Regions: {regions.count()}')
            
            if regions.exists():
                for region in regions:
                    region_lfas = region.localfootballassociation_set.count()
                    self.stdout.write(f'     ID {region.id}: {region.name} ({region_lfas} LFAs)')
                    total_lfas += region_lfas
            else:
                self.stdout.write(f'     ❌ No regions found')
            
            total_regions += regions.count()
        
        self.stdout.write(f'\n📊 Summary:')
        self.stdout.write(f'   Total Regions: {total_regions}/52')
        self.stdout.write(f'   Total LFAs: {total_lfas}/341')
        
        # Show next available region ID
        if total_regions < 52:
            from django.db import models
            last_region_id = Region.objects.aggregate(models.Max('id'))['id__max'] or 0
            self.stdout.write(f'   Next Region ID: {last_region_id + 1}')
