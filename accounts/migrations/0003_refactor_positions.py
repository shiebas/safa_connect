from django.db import migrations, models

def convert_levels_to_string(apps, schema_editor):
    """Convert position level to levels string"""
    Position = apps.get_model('accounts', 'Position')
    
    for position in Position.objects.all():
        # Make sure position has a default level value
        if not position.levels:
            position.levels = 'NATIONAL,PROVINCE,REGION,LFA,CLUB'
            position.save()

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_update_position_titles'),
    ]

    operations = [
        # Add new levels field
        migrations.AddField(
            model_name='position',
            name='levels',
            field=models.CharField(default='NATIONAL,PROVINCE,REGION,LFA,CLUB', help_text='Comma-separated list of levels where this position can be used', max_length=100),
        ),
        
        # Make title unique
        migrations.AlterField(
            model_name='position',
            name='title',
            field=models.CharField(max_length=100, unique=True),
        ),
        # Change model options
        migrations.AlterModelOptions(
            name='position',
            options={'ordering': ['title']},
        ),
        # Skip constraint removal as it may not exist in some databases
        # migrations.RemoveConstraint(
        #     model_name='position',
        #     name='unique_title_per_level',
        # ),
    ]
