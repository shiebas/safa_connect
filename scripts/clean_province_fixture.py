import json
import sys

# Usage: python scripts/clean_province_fixture.py input.json output.json
if len(sys.argv) != 3:
    print("Usage: python scripts/clean_province_fixture.py input.json output.json")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

# Only keep these fields (adjust as needed for your model)
ALLOWED_FIELDS = {
    "name", "code", "description", "safa_id", "country", "national_federation", "logo", "created", "modified"
}

with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

for obj in data:
    fields = obj["fields"]
    # Remove any field not in ALLOWED_FIELDS
    keys_to_remove = [k for k in fields if k not in ALLOWED_FIELDS]
    for k in keys_to_remove:
        del fields[k]

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print(f"Cleaned fixture written to {output_file}")
