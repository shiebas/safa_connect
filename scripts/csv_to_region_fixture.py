import csv
import json
import sys

# Usage: python scripts/csv_to_region_fixture.py geography/fixtures/geography_region.csv geography.region geography/fixtures/geography_region.json
if len(sys.argv) != 4:
    print("Usage: python scripts/csv_to_region_fixture.py input.csv app_label.model_name output.json")
    sys.exit(1)

csv_file = sys.argv[1]
model_name = sys.argv[2]
json_file = sys.argv[3]

with open(csv_file, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    objects = []
    for row in reader:
        # Use the CSV id as pk, and province_id as the foreign key
        fields = {
            "name": row.get("name", ""),
            "code": row.get("code", ""),
            "province": int(row["province_id"]) if row.get("province_id") else None,
            "description": row.get("description", ""),
            "created": row.get("created", "2025-01-01T00:00:00"),
            "modified": row.get("modified", "2025-01-01T00:00:00")
        }
        # Omit safa_id entirely (do not include it in fields)
        obj = {
            "model": model_name,
            "pk": int(row["id"]),
            "fields": fields
        }
        objects.append(obj)

with open(json_file, 'w', encoding='utf-8') as f:
    json.dump(objects, f, indent=2)

print(f"Converted {csv_file} to {json_file} as model {model_name}")
