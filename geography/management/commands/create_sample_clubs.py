from django.core.management.base import BaseCommand
from django.db import transaction
from geography.models import Club, LocalFootballAssociation, Region

class Command(BaseCommand):
    help = 'Create sample clubs for testing registration system'
    
    def add_arguments(self, parser):
        parser.add_argument('--clubs-per-lfa', type=int, default=2, help='Number of clubs per LFA')
    
    def handle(self, *args, **options):
        clubs_per_lfa = options['clubs_per_lfa']
        
        self.stdout.write('🏟️  Creating sample clubs for testing...')
        
        # Club name templates
        club_names = [
            '{} United FC', '{} City FC', '{} Rovers FC', '{} Athletic FC',
            '{} FC', '{} Town FC', '{} United', '{} City',
            '{} Eagles FC', '{} Lions FC', '{} Chiefs FC', '{} Pirates FC'
        ]
        
        try:
            with transaction.atomic():
                created_count = 0
                
                # Get first 10 LFAs for testing
                lfas = LocalFootballAssociation.objects.all()[:10]
                
                for lfa in lfas:
                    for i in range(clubs_per_lfa):
                        club_name_template = club_names[i % len(club_names)]
                        # Use LFA name without "SAFA" and "LFA" 
                        base_name = lfa.name.replace('SAFA ', '').replace(' LFA', '')
                        club_name = club_name_template.format(base_name)
                        
                        # Check if club already exists
                        if not Club.objects.filter(name=club_name).exists():
                            club = Club.objects.create(
                                name=club_name,
                                code=f"{base_name[:3].upper()}{i+1:02d}",
                                localfootballassociation=lfa,
                                status='ACTIVE',
                                stadium=f'{base_name} Stadium',
                                colors=f'Blue and White',
                                description=f'Football club from {lfa.name}',
                                payment_confirmed=True  # So they get SAFA IDs
                            )
                            created_count += 1
                            self.stdout.write(f'  ✅ {club.name} (SAFA ID: {club.safa_id})')
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n🎉 Sample clubs created!\n'
                        f'   Total clubs: {created_count}\n'
                        f'   Across {len(lfas)} LFAs\n'
                        f'   Now test club registration at: /accounts/register/club/'
                    )
                )
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
