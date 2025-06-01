from django.db import migrations, models
from django.db.models import Q
import random
import string

def generate_unique_safa_id(used_ids):
    """Generate a unique SAFA ID not in the used_ids set"""
    chars = string.ascii_uppercase + string.digits
    max_attempts = 100
    
    for _ in range(max_attempts):
        # Generate a random 5-character string
        safa_id = ''.join(random.choice(chars) for _ in range(5))
        
        if safa_id not in used_ids:
            used_ids.add(safa_id)
            return safa_id
    
    raise ValueError("Could not generate a unique SAFA ID after multiple attempts")

def populate_safa_ids(apps, schema_editor):
    # Get all models that need SAFA IDs
    NationalFederation = apps.get_model('geography', 'NationalFederation')
    Association = apps.get_model('geography', 'Association')
    Region = apps.get_model('geography', 'Region')
    LocalFootballAssociation = apps.get_model('geography', 'LocalFootballAssociation')
    Club = apps.get_model('geography', 'Club')
    
    # Get all existing SAFA IDs across all models to avoid duplicates
    used_ids = set()
    for model in [NationalFederation, Association, Region, LocalFootballAssociation, Club]:
        existing_ids = model.objects.exclude(safa_id='').values_list('safa_id', flat=True)
        used_ids.update(existing_ids)
    
    # Helper function to safely get objects needing IDs (handles both empty strings and nulls)
    def needs_id(queryset):
        return queryset.filter(Q(safa_id='') | Q(safa_id__isnull=True))
    
    # Process models one by one, collecting and using existing IDs
    for model_name, model_class in [
        ('NationalFederation', NationalFederation),
        ('Association', Association),
        ('Region', Region),
        ('LocalFootballAssociation', LocalFootballAssociation),
        ('Club', Club)
    ]:
        # Get records needing SAFA IDs
        for obj in needs_id(model_class.objects):
            tries = 0
            while tries < 5:  # Limit attempts per object
                try:
                    safa_id = generate_unique_safa_id(used_ids)
                    obj.safa_id = safa_id
                    obj.save(update_fields=['safa_id'])
                    break  # Success, move to next object
                except Exception as e:
                    tries += 1
                    if tries >= 5:
                        print(f"Failed to set SAFA ID for {model_name} #{obj.id}: {str(e)}")

def reverse_populate(apps, schema_editor):
    # No need to remove IDs
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('geography', '0013_association_safa_id_club_safa_id_and_more'),  # Updated to reference the actual migration
    ]

    operations = [
        # First make safa_id nullable to avoid constraint failures
        migrations.AlterField(
            model_name='nationalfederation',
            name='safa_id',
            field=models.CharField(blank=True, null=True, help_text='Unique 5-character SAFA identifier', max_length=5, unique=True, verbose_name='SAFA ID'),
        ),
        migrations.AlterField(
            model_name='association',
            name='safa_id',
            field=models.CharField(blank=True, null=True, help_text='Unique 5-character SAFA identifier', max_length=5, unique=True, verbose_name='SAFA ID'),
        ),
        migrations.AlterField(
            model_name='region',
            name='safa_id',
            field=models.CharField(blank=True, null=True, help_text='Unique 5-character SAFA identifier', max_length=5, unique=True, verbose_name='SAFA ID'),
        ),
        migrations.AlterField(
            model_name='localfootballassociation',
            name='safa_id',
            field=models.CharField(blank=True, null=True, help_text='Unique 5-character SAFA identifier', max_length=5, unique=True, verbose_name='SAFA ID'),
        ),
        migrations.AlterField(
            model_name='club',
            name='safa_id',
            field=models.CharField(blank=True, null=True, help_text='Unique 5-character SAFA identifier', max_length=5, unique=True, verbose_name='SAFA ID'),
        ),
        # Then populate IDs
        migrations.RunPython(populate_safa_ids, reverse_populate),
    ]