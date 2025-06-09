from django.core.management.base import BaseCommand
from django.db import transaction
from geography.models import Province, Region

class Command(BaseCommand):
    help = 'Create Gauteng regions with correct IDs'
    
    def handle(self, *args, **options):
        try:
            province = Province.objects.get(name='Gauteng')
            
            # Gauteng regions (5 regions starting from ID 14)
            gauteng_regions = [
                'Ekurhuleni',          # ID 14
                'Johannesburg',        # ID 15  
                'Sedibeng',           # ID 16
                'Tshwane',            # ID 17
                'West Rand'           # ID 18
            ]
            
            self.stdout.write(f'🔧 Creating Gauteng regions...')
            
            with transaction.atomic():
                # Delete existing Gauteng regions if any
                existing_count = Region.objects.filter(province=province).count()
                if existing_count > 0:
                    Region.objects.filter(province=province).delete()
                    self.stdout.write(f'🗑️  Deleted {existing_count} existing regions')
                
                # Create new regions starting from ID 14
                region_id = 14
                for region_name in gauteng_regions:
                    region = Region(
                        id=region_id,
                        name=region_name,
                        province=province
                    )
                    region.save()
                    self.stdout.write(f'   ✅ Created ID {region_id}: {region_name}')
                    region_id += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f'\n🎉 Created {len(gauteng_regions)} Gauteng regions (IDs 14-18)')
                )
                
        except Province.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ Gauteng province not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
