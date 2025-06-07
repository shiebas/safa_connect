from django.core.management.base import BaseCommand
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Generate new SAFA IDs for users without one'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Force regenerate all IDs')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        
        if force:
            users = CustomUser.objects.all()
            self.stdout.write(self.style.WARNING("Force mode: Regenerating all user SAFA IDs"))
        else:
            users = CustomUser.objects.filter(safa_id__isnull=True)
            self.stdout.write(self.style.SUCCESS(f"Found {users.count()} users without SAFA IDs"))
            
        count = 0
        for user in users:
            original_id = user.safa_id
            
            if not dry_run:
                user.generate_safa_id()
                user.save(update_fields=['safa_id'])
                count += 1
                new_id = user.safa_id
            else:
                new_id = "DRY-RUN"
                
            self.stdout.write(self.style.SUCCESS(
                f"User {user.email}: {original_id or 'None'} → {new_id}"
            ))
            
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: No changes were made"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Completed: {count} users updated."))
