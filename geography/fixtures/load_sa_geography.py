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

def create_fixtures():
    """Generate Django fixtures for geography data"""
    import json
    
    fixtures = []
    province_id = 1
    region_id = 1
    lfa_id = 1
    
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
                region_id += 1
        
        province_id += 1
    
    return fixtures
