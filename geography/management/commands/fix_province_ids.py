from django.core.management.base import BaseCommand
from django.db import transaction
from geography.models import Province, Region, LocalFootballAssociation

class Command(BaseCommand):
    help = 'Fix province IDs to be sequential 1-9'
    
    def handle(self, *args, **options):
        self.stdout.write('🔧 Fixing province ID sequence...')
        
        # Expected province order (1-9)
        expected_provinces = [
            'Eastern Cape',
            'Free State', 
            'Gauteng',
            'KwaZulu-Natal',
            'Limpopo',
            'Mpumalanga',
            'Northern Cape',
            'North West',
            'Western Cape'
        ]
        
        try:
            with transaction.atomic():
                # Get all provinces ordered by name
                provinces = Province.objects.all().order_by('name')
                
                self.stdout.write(f'Found {provinces.count()} provinces')
                
                # Show current IDs
                for province in provinces:
                    self.stdout.write(f'  Current: ID {province.id} - {province.name}')
                
                # Create a mapping of correct IDs
                province_mapping = {}
                
                for i, province_name in enumerate(expected_provinces, 1):
                    try:
                        province = Province.objects.get(name=province_name)
                        province_mapping[province.id] = i
                        self.stdout.write(f'  Will change: {province.name} from ID {province.id} to ID {i}')
                    except Province.DoesNotExist:
                        self.stdout.write(f'  ❌ Missing province: {province_name}')
                
                # Update in reverse order to avoid conflicts
                for old_id, new_id in sorted(province_mapping.items(), reverse=True):
                    province = Province.objects.get(id=old_id)
                    
                    # Temporarily set to negative ID to avoid conflicts
                    temp_id = -new_id
                    province.id = temp_id
                    province.save()
                    self.stdout.write(f'  Temp: {province.name} -> ID {temp_id}')
                
                # Now set to correct positive IDs
                for old_id, new_id in province_mapping.items():
                    province = Province.objects.get(id=-new_id)
                    province.id = new_id
                    province.save()
                    self.stdout.write(f'  ✅ Fixed: {province.name} -> ID {new_id}')
                
                # Verify the fix
                self.stdout.write('\n📊 Final province sequence:')
                for province in Province.objects.all().order_by('id'):
                    regions_count = province.region_set.count()
                    lfas_count = LocalFootballAssociation.objects.filter(region__province=province).count()
                    self.stdout.write(f'  ID {province.id}: {province.name} ({regions_count} regions, {lfas_count} LFAs)')
                
                self.stdout.write(
                    self.style.SUCCESS('\n✅ Province IDs fixed successfully!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error fixing province IDs: {str(e)}')
            )
