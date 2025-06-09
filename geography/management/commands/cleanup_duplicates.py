from django.core.management.base import BaseCommand
from geography.models import Province, Region, LocalFootballAssociation
from django.db.models import Count

class Command(BaseCommand):
    help = 'Clean up duplicate geography data and show current status'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Actually fix the duplicates (otherwise just show them)',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('🔍 Checking for duplicate geography data...')
        
        # Check for duplicate provinces
        duplicate_provinces = Province.objects.values('name').annotate(
            count=Count('name')
        ).filter(count__gt=1)
        
        if duplicate_provinces:
            self.stdout.write('❌ Found duplicate provinces:')
            for dup in duplicate_provinces:
                provinces = Province.objects.filter(name=dup['name'])
                self.stdout.write(f'  {dup["name"]}: {dup["count"]} copies')
                
                if options['fix']:
                    # Keep the first one, delete the rest
                    keep = provinces.first()
                    for province in provinces[1:]:
                        # Move regions to the first province
                        province.region_set.all().update(province=keep)
                        province.delete()
                        self.stdout.write(f'    ✅ Deleted duplicate {province.name}')
        else:
            self.stdout.write('✅ No duplicate provinces found')
        
        # Check for duplicate regions
        duplicate_regions = Region.objects.values('name', 'province').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if duplicate_regions:
            self.stdout.write('❌ Found duplicate regions:')
            for dup in duplicate_regions:
                regions = Region.objects.filter(
                    name=dup['name'], 
                    province_id=dup['province']
                )
                province_name = regions.first().province.name
                self.stdout.write(f'  {dup["name"]} in {province_name}: {dup["count"]} copies')
                
                if options['fix']:
                    # Keep the first one, delete the rest
                    keep = regions.first()
                    for region in regions[1:]:
                        # Move LFAs to the first region
                        region.localfootballassociation_set.all().update(region=keep)
                        region.delete()
                        self.stdout.write(f'    ✅ Deleted duplicate {region.name}')
        else:
            self.stdout.write('✅ No duplicate regions found')
        
        # Show current status
        self.stdout.write('\n📊 Current SAFA structure:')
        provinces = Province.objects.all()
        total_regions = 0
        total_lfas = 0
        
        for province in provinces:
            regions_count = province.region_set.count()
            lfas_count = LocalFootballAssociation.objects.filter(region__province=province).count()
            total_regions += regions_count
            total_lfas += lfas_count
            self.stdout.write(f'  {province.name}: {regions_count} regions, {lfas_count} LFAs')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ SUMMARY:\n'
                f'   Provinces: {provinces.count()}\n'
                f'   Regions: {total_regions}\n'
                f'   LFAs: {total_lfas}'
            )
        )
        
        if not options['fix'] and (duplicate_provinces or duplicate_regions):
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  Run with --fix to clean up duplicates'
                )
            )
