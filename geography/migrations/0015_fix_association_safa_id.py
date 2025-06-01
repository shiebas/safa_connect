from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('geography', '0014_populate_safa_ids'),  # Add this migration as a dependency
    ]

    operations = [
        # First make safa_id nullable to avoid constraint failures
        migrations.AlterField(
            model_name='association',
            name='safa_id',
            field=models.CharField(blank=True, null=True, help_text='Unique 5-character SAFA identifier', max_length=5, unique=True, verbose_name='SAFA ID'),
        ),
    ]