from django.core.management.base import BaseCommand
from accounts.models import CustomUser
import re

class Command(BaseCommand):
    help = 'Validates all names in the CustomUser model'

    def handle(self, *args, **options):
        self.stdout.write('Starting name validation...')
        invalid_users = []
        for user in CustomUser.objects.all():
            if not self.is_valid_name(user.first_name) or not self.is_valid_name(user.last_name):
                invalid_users.append(user)
                self.stdout.write(self.style.ERROR(f'Invalid name for user {user.email}: {user.first_name} {user.last_name}'))
        
        if not invalid_users:
            self.stdout.write(self.style.SUCCESS('All names are valid.'))
        else:
            self.stdout.write(self.style.WARNING(f'{len(invalid_users)} users found with invalid names.'))

    def is_valid_name(self, name):
        if not name or len(name) < 3 or not re.match(r'^[a-zA-Z]+$', name):
            return False
        return True
