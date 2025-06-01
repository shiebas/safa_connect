from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('geography', '0012_add_fields_to_club'),
    ]

    operations = [
        # Add safa_id field to all models as nullable first
        migrations.AddField(
            model_name='nationalfederation',
            name='safa_id',
            field=models.CharField(blank=True, null=True, help_text='Unique 5-character SAFA identifier', max_length=5, unique=True, verbose_name='SAFA ID'),
        ),
        migrations.AddField(
            model_name='association',
            name='safa_id',
            field=models.CharField(blank=True, null=True, help_text='Unique 5-character SAFA identifier', max_length=5, unique=True, verbose_name='SAFA ID'),
        ),
        migrations.AddField(
            model_name='region',
            name='safa_id',
            field=models.CharField(blank=True, null=True, help_text='Unique 5-character SAFA identifier', max_length=5, unique=True, verbose_name='SAFA ID'),
        ),
        migrations.AddField(
            model_name='localfootballassociation',
            name='safa_id',
            field=models.CharField(blank=True, null=True, help_text='Unique 5-character SAFA identifier', max_length=5, unique=True, verbose_name='SAFA ID'),
        ),
        migrations.AddField(
            model_name='club',
            name='safa_id',
            field=models.CharField(blank=True, null=True, help_text='Unique 5-character SAFA identifier', max_length=5, unique=True, verbose_name='SAFA ID'),
        ),
    ]