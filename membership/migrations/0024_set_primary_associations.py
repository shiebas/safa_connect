from django.db import migrations

def set_primary_associations(apps, schema_editor):
    """
    Set the primary_association field for all officials based on:
    1. First, try to set to SAFRA (ID 11)
    2. If not found, use the first association in the ManyToMany relationship
    """
    Official = apps.get_model('membership', 'Official')
    Association = apps.get_model('geography', 'Association')
    
    # Try to get SAFRA
    try:
        safra = Association.objects.filter(id=11).first()
    except:
        safra = None
    
    # Get all officials
    officials = Official.objects.all()
    
    # Set primary_association for each official
    for official in officials:
        if not official.primary_association:
            if safra:
                # Set SAFRA as primary association
                official.primary_association = safra
                official.save(update_fields=['primary_association'])
                
                # Also ensure it's in the M2M relationship
                if not official.associations.filter(id=11).exists():
                    official.associations.add(safra)
            else:
                # No SAFRA found, try to use the first association in the M2M
                first_association = official.associations.first()
                if first_association:
                    official.primary_association = first_association
                    official.save(update_fields=['primary_association'])

class Migration(migrations.Migration):

    dependencies = [
        ('membership', '0023_add_official_primary_association'),
    ]

    operations = [
        migrations.RunPython(set_primary_associations, reverse_code=migrations.RunPython.noop),
    ]
