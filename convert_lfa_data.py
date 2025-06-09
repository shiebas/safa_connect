import json
from datetime import datetime

def convert_lfa_data():
    """Convert the provided LFA JSON data to Django fixture format"""
    
    # Your LFA data (first few entries as example)
    lfa_raw_data = [
        {
            "acronym": "MAT",
            "association_id": None,
            "created": "2025-05-30 22:41:44.797220",
            "description": "",
            "headquarters": "",
            "id": 1,
            "logo": "logos/SAFA_logo_mGrrpQ1.svg.png",
            "modified": "2025-06-02 07:30:15.324968",
            "name": "MATATIELE LFA",
            "region_id": 1,
            "safa_id": "KCUUF",
            "website": ""
        }
        # ... (all 347 LFAs would be here)
    ]
    
    django_fixtures = []
    
    for lfa in lfa_raw_data:
        # Convert datetime format
        created = datetime.fromisoformat(lfa['created'].replace(' ', 'T')).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        modified = datetime.fromisoformat(lfa['modified'].replace(' ', 'T')).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        fixture = {
            "model": "geography.localfootballassociation",
            "pk": lfa['id'],
            "fields": {
                "acronym": lfa['acronym'],
                "association_id": lfa['association_id'],
                "created": created,
                "description": lfa['description'],
                "headquarters": lfa['headquarters'],
                "logo": lfa['logo'],
                "modified": modified,
                "name": lfa['name'],
                "region": lfa['region_id'],
                "safa_id": lfa['safa_id'],
                "website": lfa['website']
            }
        }
        django_fixtures.append(fixture)
    
    # Save to fixture file
    with open('geography/fixtures/geography_localfootballassociation.json', 'w') as f:
        json.dump(django_fixtures, f, indent=2)
    
    print(f"Converted {len(django_fixtures)} LFAs to Django fixture format")
    
    # Show LFA count by region for verification
    region_counts = {}
    for lfa in lfa_raw_data:
        region_id = lfa['region_id']
        region_counts[region_id] = region_counts.get(region_id, 0) + 1
    
    print("\nLFAs per region:")
    for region_id in sorted(region_counts.keys()):
        print(f"Region {region_id}: {region_counts[region_id]} LFAs")

if __name__ == '__main__':
    convert_lfa_data()
