from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0021_alter_customuser_role"),
    ]

    operations = [
        # No DB field added, age is a property. This migration is a marker for the code change.
    ]
