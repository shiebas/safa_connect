from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tournament_verification.tournament_models import TournamentCompetition, SportCode

class Command(BaseCommand):
    help = 'Creates a simple test tournament using existing sport codes'

    def handle(self, *args, **kwargs):
        # Get existing Soccer sport code
        try:
            soccer = SportCode.objects.get(code='SOCCER')
            self.stdout.write(f'Using existing sport code: {soccer.name}')
        except SportCode.DoesNotExist:
            self.stdout.write(self.style.ERROR('Soccer sport code not found. Please run: python manage.py setup_sport_codes'))
            return
        
        # Create test tournament
        start_date = timezone.now() + timedelta(days=7)  # 7 days from now
        end_date = start_date + timedelta(days=2)  # 2 days duration
        registration_deadline = timezone.now() + timedelta(days=5)  # 5 days from now
        
        # Get a superuser for the organizer field
        from django.contrib.auth import get_user_model
        User = get_user_model()
        organizer = User.objects.filter(is_superuser=True).first()
        
        if not organizer:
            self.stdout.write(self.style.ERROR('No superuser found. Please create a superuser first.'))
            return
        
        tournament, created = TournamentCompetition.objects.get_or_create(
            name='Test Soccer Tournament 2024',
            defaults={
                'description': 'A test tournament for registration and camera verification testing',
                'sport_code': soccer,
                'tournament_type': 'ROUND_ROBIN',
                'start_date': start_date,
                'end_date': end_date,
                'location': 'Test Sports Complex, Johannesburg',
                'venue_address': '123 Test Street, Johannesburg, 2000',
                'max_teams': 8,
                'max_players_per_team': 15,
                'min_players_per_team': 7,
                'pool_size': 4,
                'teams_advance_from_pool': 2,
                'registration_deadline': registration_deadline,
                'registration_fee': 0.00,
                'is_registration_open': True,
                'is_active': True,
                'is_published': True,
                'organizer': organizer
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
