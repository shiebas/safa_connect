from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tournament_verification.tournament_models import TournamentCompetition, SportCode

class Command(BaseCommand):
    help = 'Creates a test tournament for registration testing'

    def handle(self, *args, **kwargs):
        # Get or create Soccer sport code
        soccer, created = SportCode.objects.get_or_create(
            code='SOCCER',
            defaults={
                'name': 'Soccer',
                'players_per_team': 11,
                'match_duration_minutes': 90,
                'has_extra_time': True,
                'has_penalties': True,
                'description': 'Association Football'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created sport code: {soccer.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Sport code already exists: {soccer.name}'))
        
        # Create test tournament
        start_date = timezone.now() + timedelta(days=7)  # 7 days from now
        end_date = start_date + timedelta(days=2)  # 2 days duration
        registration_deadline = timezone.now() + timedelta(days=5)  # 5 days from now
        
        tournament, created = TournamentCompetition.objects.get_or_create(
            name='Test Soccer Tournament 2024',
            defaults={
                'description': 'A test tournament for registration and camera verification testing',
                'sport_code': soccer,
                'tournament_type': 'ROUND_ROBIN',
                'start_date': start_date,
                'end_date': end_date,
                'location': 'Test Sports Complex, Johannesburg',
                'max_teams': 8,
                'registration_deadline': registration_deadline,
                'is_active': True,
                'is_published': True,
                'allow_walk_in_registration': True,
                'registration_fee': 0.00,
                'requires_photo_verification': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Successfully created tournament: {tournament.name}'))
            self.stdout.write(f'  - Start Date: {tournament.start_date}')
            self.stdout.write(f'  - Registration Deadline: {tournament.registration_deadline}')
            self.stdout.write(f'  - Location: {tournament.location}')
            self.stdout.write(f'  - Sport: {tournament.sport_code.name}')
            self.stdout.write(f'  - Registration URL: /tournaments/register/{tournament.id}/')
        else:
            self.stdout.write(self.style.WARNING(f'Tournament already exists: {tournament.name}'))
        
        self.stdout.write(self.style.SUCCESS('Test tournament setup complete!'))
