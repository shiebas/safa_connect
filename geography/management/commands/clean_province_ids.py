from django.core.management.base import BaseCommand
from django.db import transaction
from geography.models import Province, Region, LocalFootballAssociation

class Command(BaseCommand):
    help = 'Delete duplicate province records, keep only IDs 1-9'
    
    def handle(self, *args, **options):
        self.stdout.write('🧹 Cleaning up province IDs...')
        
        try:
            with transaction.atomic():
                # Show what we have before cleanup
                all_provinces = Province.objects.all().order_by('id')
                self.stdout.write(f'Found {all_provinces.count()} total provinces:')
                for p in all_provinces:
                    self.stdout.write(f'  ID {p.id}: {p.name}')
                
                # Delete provinces with negative IDs (-1 to -9)
                negative_provinces = Province.objects.filter(id__lt=0)
                if negative_provinces.exists():
                    self.stdout.write(f'\n❌ Deleting {negative_provinces.count()} provinces with negative IDs:')
                    for p in negative_provinces:
                        self.stdout.write(f'  Deleting ID {p.id}: {p.name}')
                    negative_provinces.delete()
                
                # Delete provinces with IDs 10-18
                high_provinces = Province.objects.filter(id__gte=10, id__lte=18)
                if high_provinces.exists():
                    self.stdout.write(f'\n❌ Deleting {high_provinces.count()} provinces with IDs 10-18:')
                    for p in high_provinces:
                        self.stdout.write(f'  Deleting ID {p.id}: {p.name}')
                    high_provinces.delete()
                
                # Show final result
                final_provinces = Province.objects.all().order_by('id')
                self.stdout.write(f'\n✅ Final provinces (should be IDs 1-9):')
                for p in final_provinces:
                    regions_count = p.region_set.count()
                    lfas_count = LocalFootballAssociation.objects.filter(region__province=p).count()
                    self.stdout.write(f'  ID {p.id}: {p.name} ({regions_count} regions, {lfas_count} LFAs)')
                
                self.stdout.write(
                    self.style.SUCCESS(f'\n🎉 Cleanup complete! {final_provinces.count()} provinces remaining.')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during cleanup: {str(e)}')
            )
