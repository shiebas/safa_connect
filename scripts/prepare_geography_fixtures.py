import json
import os

def process_fixture(filename, model_name, field_mappings=None):
    if field_mappings is None:
        field_mappings = {}

    backup_path = f'databackup29072025/{filename}.json'
    fixture_path = f'geography/fixtures/{filename}.json'

    try:
        with open(backup_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Skipping {backup_path}, not found.")
        return

    fixture_data = []
    for record in data:
        pk = record.get('id')
        if pk is None:
            continue

        fields = record.copy()

        # Apply field mappings
        for old_key, new_key in field_mappings.items():
            if old_key in fields:
                fields[new_key] = fields.pop(old_key)

        # The DeserializationError seems to be because the fixture format is non-standard.
        # The original fixture had `_id` suffixes for foreign keys, and `id` in fields.
        # Let's replicate that.

        final_fields = {}
        for key, value in fields.items():
            if isinstance(value, dict): # handle nested objects if any
                continue
            final_fields[key] = str(value) if isinstance(value, int) else value

        fixture_data.append({
            'model': model_name,
            'pk': pk,
            'fields': final_fields
        })

    with open(fixture_path, 'w') as f:
        json.dump(fixture_data, f, indent=2)
    print(f"Generated fixture: {fixture_path}")

if __name__ == '__main__':
    process_fixture('geography_worldsportsbody', 'geography.worldsportsbody')
    process_fixture('geography_continent', 'geography.continent')
    process_fixture('geography_continentfederation', 'geography.continentfederation')
    process_fixture('geography_continentregion', 'geography.continentregion')
    process_fixture('geography_country', 'geography.country')
    process_fixture('geography_nationalfederation', 'geography.nationalfederation')

    # Special handling for province: rename country_id to national_federation_id
    process_fixture('geography_province', 'geography.province', {'country_id': 'national_federation_id'})

    process_fixture('geography_region', 'geography.region')
    process_fixture('geography_association', 'geography.association')

    # Special handling for localfootballassociation
    process_fixture('geography_localfootballassociation', 'geography.localfootballassociation')
