
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('membership', '0002_membershipseasonhistory_officialcertification_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='MemberDocument',
        ),
    ]
