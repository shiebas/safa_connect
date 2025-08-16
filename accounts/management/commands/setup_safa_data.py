from django.core.management.base import BaseCommand
from accounts.models import OrganizationType, Position
from geography.models import NationalFederation, Association

class Command(BaseCommand):
    help = 'Setup initial SAFA data'

    def handle(self, *args, **options):
        # Create organization types
        org_types = [
            ('NATIONAL', 'National Federation'),
            ('PROVINCE', 'Provincial Association'),
            ('REGION', 'Regional Association'),
            ('LFA', 'Local Football Association'),
            ('CLUB', 'Football Club'),
            ('ASSOCIATION', 'Referee/Coach Association'),
        ]
        
        for level, name in org_types:
            OrganizationType.objects.get_or_create(
                level=level,
                defaults={'name': name}
            )
            self.stdout.write(f'Created organization type: {name}')
        
        # Create default positions
        positions = [
            ('President', 'NATIONAL,PROVINCE,REGION,LFA,CLUB'),
            ('Vice President', 'NATIONAL,PROVINCE,REGION,LFA,CLUB'),
            ('Secretary General', 'NATIONAL,PROVINCE,REGION,LFA'),
            ('Treasurer', 'NATIONAL,PROVINCE,REGION,LFA,CLUB'),
            ('Technical Director', 'NATIONAL,PROVINCE,REGION,LFA'),
            ('Referee', 'ASSOCIATION'),
            ('Assistant Referee', 'ASSOCIATION'),
            ('Coach', 'CLUB'),
            ('Manager', 'CLUB'),
            ('Administrator', 'NATIONAL,PROVINCE,REGION,LFA,CLUB'),
        ]
        
        for title, levels in positions:
            Position.objects.get_or_create(
                title=title,
                defaults={
                    'levels': levels,
                    'employment_type': 'MEMBER',
                    'is_active': True
                }
            )
            self.stdout.write(f'Created position: {title}')
        
        # Create SAFA National Federation
        NationalFederation.objects.get_or_create(
            name='South African Football Association',
            defaults={
                'acronym': 'SAFA',
                'country_id': 1  # Assuming South Africa has ID 1
            }
        )
        self.stdout.write('Created SAFA National Federation')
        
        # Create default referee association
        try:
            safa = NationalFederation.objects.get(acronym='SAFA')
            Association.objects.get_or_create(
                name='SAFA Referees Association',
                defaults={
                    'acronym': 'SAFRA',
                    'national_federation': safa,
                    'type': 'REFEREE'
                }
            )
            self.stdout.write('Created SAFRA')
        except Exception as e:
            self.stdout.write(f'Error creating SAFRA: {e}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully setup initial SAFA data')
        )