from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_add_position_levels_field'),
    ]

    operations = [
        # This migration is an empty operation that records that we manually 
        # removed the level field outside of Django's migration system
        migrations.RunSQL(
            # No-op: the column has already been removed manually
            "",
            # No-op reverse migration
            ""
        ),
    ]
