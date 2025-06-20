from django.db import migrations, models


def convert_level_to_levels(apps, schema_editor):
    """Set default levels for all positions"""
    Position = apps.get_model('accounts', 'Position')
    
    for position in Position.objects.all():
        if not position.levels:
            position.levels = 'NATIONAL,PROVINCE,REGION,LFA,CLUB'
            position.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_update_position_titles'),
    ]

    operations = [
        # Add the levels field
        migrations.AddField(
            model_name='position',
            name='levels',
            field=models.CharField(default='NATIONAL,PROVINCE,REGION,LFA,CLUB', help_text='Comma-separated list of levels where this position can be used', max_length=100),
        ),
        # Run data migration to copy level to levels
        migrations.RunPython(convert_level_to_levels),
    ]
