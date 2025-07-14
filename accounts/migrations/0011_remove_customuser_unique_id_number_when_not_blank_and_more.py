from django.db import migrations, models

def handle_duplicate_mother_bodies(apps, schema_editor):
    CustomUser = apps.get_model('accounts', 'CustomUser')
    # Find and handle duplicates
    from django.db.models import Count
    duplicates = (CustomUser.objects
                 .values('mother_body')
                 .annotate(count=Count('id'))
                 .filter(count__gt=1, mother_body__isnull=False))
    
    for duplicate in duplicates:
        mother_body_id = duplicate['mother_body']
        # Keep the first user and nullify others
        users = CustomUser.objects.filter(mother_body=mother_body_id).order_by('id')
        first_user = users.first()
        users.exclude(id=first_user.id).update(mother_body=None)

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_document_access_log'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='customuser',
            name='unique_id_number_when_not_blank',
        ),
        migrations.RemoveConstraint(
            model_name='customuser',
            name='unique_passport_number_when_not_blank',
        ),
        migrations.RunPython(handle_duplicate_mother_bodies),
        migrations.AddConstraint(
            model_name='customuser',
            constraint=models.UniqueConstraint(condition=models.Q(('id_number__isnull', False)), fields=('id_number',), name='unique_id_number'),
        ),
        migrations.AddConstraint(
            model_name='customuser',
            constraint=models.UniqueConstraint(condition=models.Q(('passport_number__isnull', False)), fields=('passport_number',), name='unique_passport_number'),
        ),
        migrations.AddConstraint(
            model_name='customuser',
            constraint=models.UniqueConstraint(condition=models.Q(('mother_body__isnull', False)), fields=('mother_body',), name='unique_mother_body'),
        ),
        migrations.AlterModelTable(
            name='customuser',
            table='custom_user',
        ),
    ]
