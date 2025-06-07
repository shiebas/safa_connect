import os
import django
import sqlite3

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_global.settings')
django.setup()

# Get database path from settings
from django.conf import settings
db_path = settings.DATABASES['default']['NAME']

# Connect directly to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the province field exists in accounts_customuser
cursor.execute("PRAGMA table_info(accounts_customuser)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

# If province_id doesn't exist, add it
if 'province_id' not in column_names:
    print("Adding province_id field to accounts_customuser")
    cursor.execute("ALTER TABLE accounts_customuser ADD COLUMN province_id INTEGER REFERENCES geography_province(id)")

# Same for other fields
if 'region_id' not in column_names:
    print("Adding region_id field to accounts_customuser")
    cursor.execute("ALTER TABLE accounts_customuser ADD COLUMN region_id INTEGER REFERENCES geography_region(id)")

if 'local_federation_id' not in column_names:
    print("Adding local_federation_id field to accounts_customuser")
    cursor.execute("ALTER TABLE accounts_customuser ADD COLUMN local_federation_id INTEGER REFERENCES geography_localfootballassociation(id)")

if 'club_id' not in column_names:
    print("Adding club_id field to accounts_customuser")
    cursor.execute("ALTER TABLE accounts_customuser ADD COLUMN club_id INTEGER REFERENCES membership_club(id)")

# Commit changes and close connection
conn.commit()
conn.close()

print("Database updated successfully!")