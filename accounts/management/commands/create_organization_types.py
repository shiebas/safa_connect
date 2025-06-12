from django.core.management.base import BaseCommand
from accounts.models import OrganizationType

class Command(BaseCommand):
    help = 'Creates the default organization types'

    def handle(self, *args, **kwargs):
        # Define the default organization types
        org_types = [
            {'name': 'National Federation', 'level': 'NATIONAL'},
            {'name': 'Province', 'level': 'PROVINCE'},
            {'name': 'Region', 'level': 'REGION'},
            {'name': 'Local Football Association', 'level': 'LFA'},
            {'name': 'Club', 'level': 'CLUB'},
        ]
        
        # Create each organization type if it doesn't exist
        for org_type in org_types:
            OrganizationType.objects.get_or_create(
                name=org_type['name'],
                level=org_type['level'],
                defaults={'is_active': True}
            )
            
        self.stdout.write(self.style.SUCCESS('Successfully created organization types'))
