from django.core.management.base import BaseCommand
from geography.models import Province, Region, LocalFootballAssociation, Club

class Command(BaseCommand):
    help = 'Show existing SAFA geography data structure'
    
    def handle(self, *args, **options):
        self.stdout.write('📊 Current SAFA Geography Data:')
        
        provinces = Province.objects.all()
        total_regions = 0
        total_lfas = 0
        
        for province in provinces:
            regions = province.regions.all()
            province_lfas = LocalFootballAssociation.objects.filter(region__province=province)
            
            self.stdout.write(f'\n🏛️  {province.name}')
            self.stdout.write(f'   Regions: {regions.count()}')
            
            for region in regions[:3]:  # Show first 3 regions
                region_lfas = region.localfootballassociation_set.all()
                self.stdout.write(f'     • {region.name} ({region_lfas.count()} LFAs)')
            
            if regions.count() > 3:
                self.stdout.write(f'     ... and {regions.count() - 3} more regions')
            
            total_regions += regions.count()
            total_lfas += province_lfas.count()
        
        clubs_count = Club.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📈 SUMMARY:\n'
                f'   ✅ {provinces.count()} Provinces\n'
                f'   ✅ {total_regions} Regions\n' 
                f'   ✅ {total_lfas} LFAs\n'
                f'   ✅ {clubs_count} Clubs'
            )
        )
        
        if total_regions >= 52:
            self.stdout.write(
                self.style.SUCCESS(
                    '🎉 Your SAFA structure is already complete!'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Missing some regions (expected ~52, found {total_regions})'
                )
            )
