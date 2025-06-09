import json
import os
import django
from datetime import datetime
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_global.settings')
django.setup()

from geography.models import LocalFootballAssociation, Region

def import_lfas():
    """Import Local Football Associations from JSON file"""
    
    # Load the JSON data
    json_file_path = '/home/shaun/safa_global/safa_global/geography_localfootballassociation.json'
    
    with open(json_file_path, 'r') as file:
        lfa_data = json.load(file)
    
    print(f"Found {len(lfa_data)} LFAs to import")
    
    created_count = 0
    updated_count = 0
    error_count = 0
    
    for lfa_info in lfa_data:
        try:
            # Get the region
            try:
                region = Region.objects.get(id=lfa_info['region_id'])
            except Region.DoesNotExist:
                print(f"Region with id {lfa_info['region_id']} not found for LFA {lfa_info['name']}")
                error_count += 1
                continue
            
            # Parse dates
            created_date = datetime.fromisoformat(lfa_info['created'].replace('Z', '+00:00'))
            modified_date = datetime.fromisoformat(lfa_info['modified'].replace('Z', '+00:00'))
            
            # Check if LFA already exists
            lfa, created = LocalFootballAssociation.objects.get_or_create(
                safa_id=lfa_info['safa_id'],
                defaults={
                    'name': lfa_info['name'],
                    'acronym': lfa_info['acronym'],
                    'description': lfa_info['description'],
                    'headquarters': lfa_info['headquarters'],
                    'website': lfa_info['website'],
                    'logo': lfa_info['logo'],
                    'region': region,
                    'association_id': lfa_info['association_id'],
                    'created': timezone.make_aware(created_date),
                    'modified': timezone.make_aware(modified_date),
                }
            )
            
            if created:
                created_count += 1
                print(f"Created LFA: {lfa.name} ({lfa.acronym})")
            else:
                # Update existing LFA
                lfa.name = lfa_info['name']
                lfa.acronym = lfa_info['acronym']
                lfa.description = lfa_info['description']
                lfa.headquarters = lfa_info['headquarters']
                lfa.website = lfa_info['website']
                lfa.logo = lfa_info['logo']
                lfa.region = region
                lfa.association_id = lfa_info['association_id']
                lfa.modified = timezone.make_aware(modified_date)
                lfa.save()
                updated_count += 1
                print(f"Updated LFA: {lfa.name} ({lfa.acronym})")
                
        except Exception as e:
            print(f"Error processing LFA {lfa_info.get('name', 'Unknown')}: {str(e)}")
            error_count += 1
    
    print(f"\nImport completed:")
    print(f"Created: {created_count}")
    print(f"Updated: {updated_count}")
    print(f"Errors: {error_count}")
    print(f"Total processed: {created_count + updated_count + error_count}")

if __name__ == '__main__':
    import_lfas()
