import csv
import json
import sys

# Usage: python csv_to_json_fixture.py input.csv model_name output.json
if len(sys.argv) != 4:
    print("Usage: python csv_to_json_fixture.py input.csv app_label.model_name output.json")
    sys.exit(1)

csv_file = sys.argv[1]
model_name = sys.argv[2]
json_file = sys.argv[3]

with open(csv_file, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    objects = []
    pk = 1
    for row in reader:
        obj = {
            "model": model_name,
            "pk": pk,
            "fields": row
        }
        objects.append(obj)
        pk += 1

with open(json_file, 'w', encoding='utf-8') as f:
    json.dump(objects, f, indent=2)

print(f"Converted {csv_file} to {json_file} as model {model_name}")
