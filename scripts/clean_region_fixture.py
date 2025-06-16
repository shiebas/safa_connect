import json
import sys

# Usage: python scripts/clean_region_fixture.py input.json output.json
if len(sys.argv) != 3:
    print("Usage: python scripts/clean_region_fixture.py input.json output.json")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

for obj in data:
    fields = obj["fields"]
    if "safa_id" in fields:
        del fields["safa_id"]

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print(f"Cleaned fixture written to {output_file}")
