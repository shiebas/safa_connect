from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('geography', '0001_initial'),
        ('membership', '0010_member_organization_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='official',
            name='primary_association',
            field=models.ForeignKey(
                blank=True,
                help_text='Primary association this official belongs to',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='primary_officials',
                to='geography.association'
            ),
        ),
    ]
