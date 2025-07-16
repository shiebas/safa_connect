from django.core.management.base import BaseCommand
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Validates all ID numbers in the CustomUser model'

    def handle(self, *args, **options):
        self.stdout.write('Starting ID number validation...')
        invalid_users = []
        for user in CustomUser.objects.all():
            if user.id_number:
                if not self.is_valid_said(user.id_number):
                    invalid_users.append(user)
                    self.stdout.write(self.style.ERROR(f'Invalid ID number for user {user.email}: {user.id_number}'))
        
        if not invalid_users:
            self.stdout.write(self.style.SUCCESS('All ID numbers are valid.'))
        else:
            self.stdout.write(self.style.WARNING(f'{len(invalid_users)} users found with invalid ID numbers.'))

    def is_valid_said(self, id_number):
        if not id_number or len(id_number) != 13 or not id_number.isdigit():
            return False

        # Luhn algorithm
        sum = 0
        for i in range(12):
            digit = int(id_number[i])
            if (i % 2) == 0:
                sum += digit
            else:
                even_digit = digit * 2
                if even_digit > 9:
                    even_digit = even_digit - 9
                sum += even_digit
        last_digit = int(id_number[12])
        checksum = (10 - (sum % 10)) % 10

        return checksum == last_digit
