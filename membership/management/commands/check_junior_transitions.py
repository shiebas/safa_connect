from django.core.management.base import BaseCommand
from django.utils import timezone
from membership.models import JuniorMember
from django.db import transaction

class Command(BaseCommand):
    help = 'Check for junior members who have turned 18 and convert them to senior members'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting junior member age transition check...'))

        try:
            with transaction.atomic():
                # Get all junior members
                junior_members = JuniorMember.objects.all()
                self.stdout.write(f'Found {junior_members.count()} junior members to check')

                # Track statistics
                checked = 0
                converted = 0
                errors = 0

                # Check each junior member
                for junior in junior_members:
                    checked += 1
                    try:
                        if not junior.is_junior:  # They've turned 18
                            self.stdout.write(f'Converting {junior.get_full_name()} (ID: {junior.pk}) to senior member')
                            senior_member = junior.convert_to_senior()
                            if senior_member:
                                converted += 1
                                self.stdout.write(self.style.SUCCESS(
                                    f'Successfully converted {senior_member.get_full_name()} to senior member'
                                ))
                    except Exception as e:
                        errors += 1
                        self.stdout.write(self.style.ERROR(
                            f'Error converting {junior.get_full_name()} (ID: {junior.pk}): {str(e)}'
                        ))

                # Report results
                self.stdout.write(self.style.SUCCESS(
                    f'Age transition check completed. '
                    f'Checked: {checked}, Converted: {converted}, Errors: {errors}'
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during age transition check: {str(e)}'))
            return

        self.stdout.write(self.style.SUCCESS('Junior member age transition check completed successfully'))
