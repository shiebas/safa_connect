import json
import os

def migrate_lfa_data():
    """
    Reads LFA data from a backup file, transforms it into the Django fixture format,
    and writes it to the official fixture file.
    """
    # Define file paths
    # Assuming the script is run from the root of the repository
    backup_file_path = 'databackup29072025/geography_localfootballassociation.json'
    fixture_file_path = 'geography/fixtures/geography_localfootballassociation.json'

    # Read the backup data
    try:
        with open(backup_file_path, 'r') as f:
            backup_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Backup file not found at {backup_file_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {backup_file_path}")
        return

    new_fixture_data = []
    for record in backup_data:
        # The pk for the fixture entry
        pk = record.get('id')
        if pk is None:
            continue  # Skip records without an ID

        # Create the fields dictionary for the fixture
        fields = {
            "name": record.get("name"),
            "acronym": record.get("acronym", ""),
            "website": record.get("website", ""),
            "headquarters": record.get("headquarters", ""),
            "description": record.get("description", ""),
            "logo": record.get("logo", ""),
            "safa_id": record.get("safa_id"),
            "region": record.get("region_id"),
            "association": record.get("association_id"),
            "created": record.get("created"),
            "modified": record.get("modified"),
        }

        # Create the full fixture entry
        fixture_entry = {
            "model": "geography.localfootballassociation",
            "pk": pk,
            "fields": fields
        }
        new_fixture_data.append(fixture_entry)

    # Write the new fixture data to the file
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(fixture_file_path), exist_ok=True)
        with open(fixture_file_path, 'w') as f:
            json.dump(new_fixture_data, f, indent=2)
        print(f"Successfully migrated data to {fixture_file_path}")
    except IOError as e:
        print(f"Error writing to fixture file {fixture_file_path}: {e}")

if __name__ == "__main__":
    migrate_lfa_data()
