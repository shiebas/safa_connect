from django.core.management.base import BaseCommand
from geography.models import CustomUser

class Command(BaseCommand):
    help = 'Generate new SAFA IDs for users without one'

    def handle(self, *args, **options):
        users = CustomUser.objects.filter(safa_id__isnull=True)
        count = 0
        for user in users:
            user.generate_safa_id()
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Generated SAFA ID for {user.username}: {user.safa_id}"))
            count += 1
        self.stdout.write(self.style.SUCCESS(f"✅ Completed: {count} users updated."))
