"""
Script to create fixtures for South African football geography
Based on SAFA's actual structure
"""

# South Africa Provinces (9 provinces)
PROVINCES = [
    {'name': 'Eastern Cape', 'code': 'EC', 'capital': 'Bhisho'},
    {'name': 'Free State', 'code': 'FS', 'capital': 'Bloemfontein'},
    {'name': 'Gauteng', 'code': 'GP', 'capital': 'Johannesburg'},
    {'name': 'KwaZulu-Natal', 'code': 'KZN', 'capital': 'Pietermaritzburg'},
    {'name': 'Limpopo', 'code': 'LP', 'capital': 'Polokwane'},
    {'name': 'Mpumalanga', 'code': 'MP', 'capital': 'Mbombela'},
    {'name': 'Northern Cape', 'code': 'NC', 'capital': 'Kimberley'},
    {'name': 'North West', 'code': 'NW', 'capital': 'Mahikeng'},
    {'name': 'Western Cape', 'code': 'WC', 'capital': 'Cape Town'},
]

# Complete all 52 SAFA Regions
REGIONS = {
    'Gauteng': [
        'Johannesburg', 'Ekurhuleni', 'Tshwane', 'West Rand', 'Sedibeng', 'Vaal Triangle'
    ],
    'KwaZulu-Natal': [
        'Durban', 'Pietermaritzburg', 'Newcastle', 'Richards Bay', 'South Coast', 
        'Midlands', 'Zululand', 'Umgungundlovu'
    ],
    'Western Cape': [
        'Cape Town', 'Boland', 'Eden', 'Overberg', 'West Coast', 'Central Karoo'
    ],
    'Eastern Cape': [
        'Port Elizabeth', 'East London', 'Grahamstown', 'King Williams Town', 
        'Queenstown', 'Uitenhage', 'Border', 'Amathole'
    ],
    'Free State': [
        'Bloemfontein', 'Welkom', 'Kroonstad', 'Sasolburg', 'Bethlehem'
    ],
    'Limpopo': [
        'Polokwane', 'Tzaneen', 'Thohoyandou', 'Giyani', 'Lebowakgomo'
    ],
    'Mpumalanga': [
        'Mbombela', 'Witbank', 'Middelburg', 'Standerton', 'Secunda'
    ],
    'Northern Cape': [
        'Kimberley', 'Upington', 'Springbok', 'De Aar'
    ],
    'North West': [
        'Mahikeng', 'Rustenburg', 'Klerksdorp', 'Potchefstroom'
    ]
}

# Sample LFAs for each region (for testing)
SAMPLE_LFAS = {
    'Johannesburg': ['Johannesburg LFA', 'Soweto LFA', 'Alexandra LFA'],
    'Cape Town': ['Cape Town LFA', 'Mitchells Plain LFA', 'Khayelitsha LFA'],
    'Durban': ['Durban LFA', 'Umlazi LFA', 'Chatsworth LFA'],
    'Port Elizabeth': ['Nelson Mandela Bay LFA', 'New Brighton LFA'],
    'Bloemfontein': ['Mangaung LFA', 'Botshabelo LFA'],
    'Polokwane': ['Polokwane LFA', 'Seshego LFA'],
    # Add more as needed for testing
}

# Sample clubs for demonstration
SAMPLE_CLUBS = {
    'Johannesburg LFA': [
        'Orlando Pirates FC', 'Kaizer Chiefs FC', 'Moroka Swallows FC'
    ],
    'Cape Town LFA': [
        'Cape Town City FC', 'Ajax Cape Town FC', 'Santos FC'
    ],
    'Durban LFA': [
        'AmaZulu FC', 'Golden Arrows FC', 'Maritzburg United FC'
    ],
    # Add more for other LFAs
}

def create_fixtures():
    """Generate Django fixtures for complete geography data"""
    import json
    
    fixtures = []
    province_id = 1
    region_id = 1
    lfa_id = 1
    club_id = 1
    
    for province_data in PROVINCES:
        # Create Province fixture
        province_fixture = {
            "model": "geography.province",
            "pk": province_id,
            "fields": {
                "name": province_data['name'],
                "code": province_data['code'],
                "capital_city": province_data['capital'],
                "is_active": True
            }
        }
        fixtures.append(province_fixture)
        
        # Create Regions for this province
        if province_data['name'] in REGIONS:
            for region_name in REGIONS[province_data['name']]:
                region_fixture = {
                    "model": "geography.region",
                    "pk": region_id,
                    "fields": {
                        "name": region_name,
                        "province": province_id,
                        "is_active": True
                    }
                }
                fixtures.append(region_fixture)
                
                # Create sample LFAs for this region
                if region_name in SAMPLE_LFAS:
                    for lfa_name in SAMPLE_LFAS[region_name]:
                        lfa_fixture = {
                            "model": "geography.localfootballassociation",
                            "pk": lfa_id,
                            "fields": {
                                "name": lfa_name,
                                "region": region_id,
                                "is_active": True
                            }
                        }
                        fixtures.append(lfa_fixture)
                        
                        # Create sample clubs for this LFA
                        if lfa_name in SAMPLE_CLUBS:
                            for club_name in SAMPLE_CLUBS[lfa_name]:
                                club_fixture = {
                                    "model": "geography.club",
                                    "pk": club_id,
                                    "fields": {
                                        "name": club_name,
                                        "lfa": lfa_id,
                                        "is_active": True
                                    }
                                }
                                fixtures.append(club_fixture)
                                club_id += 1
                        
                        lfa_id += 1
                
                region_id += 1
        
        province_id += 1
    
    return fixtures

def save_fixtures_to_file():
    """Save fixtures to JSON files"""
    import json
    import os
    
    fixtures = create_fixtures()
    
    # Create fixtures directory if it doesn't exist
    fixtures_dir = os.path.dirname(__file__)
    
    # Save complete fixtures
    with open(os.path.join(fixtures_dir, 'complete_geography.json'), 'w') as f:
        json.dump(fixtures, f, indent=2)
    
    print(f"✅ Generated {len(fixtures)} fixtures")
    print("📁 Saved to: geography/fixtures/complete_geography.json")
    
    # Count by type
    provinces = [f for f in fixtures if f['model'] == 'geography.province']
    regions = [f for f in fixtures if f['model'] == 'geography.region']
    lfas = [f for f in fixtures if f['model'] == 'geography.localfootballassociation']
    clubs = [f for f in fixtures if f['model'] == 'geography.club']
    
    print(f"📊 Summary:")
    print(f"   - Provinces: {len(provinces)}")
    print(f"   - Regions: {len(regions)}")
    print(f"   - LFAs: {len(lfas)}")
    print(f"   - Clubs: {len(clubs)}")

if __name__ == "__main__":
    save_fixtures_to_file()
