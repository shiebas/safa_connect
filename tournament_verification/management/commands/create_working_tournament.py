from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tournament_verification.tournament_models import TournamentCompetition, SportCode
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates a working tournament for registration testing'

    def handle(self, *args, **kwargs):
        # Get existing Soccer sport code
        try:
            soccer = SportCode.objects.get(code='SOCCER')
            self.stdout.write(f'Using existing sport code: {soccer.name}')
        except SportCode.DoesNotExist:
            self.stdout.write(self.style.ERROR('Soccer sport code not found. Please run: python manage.py setup_sport_codes'))
            return
        
        # Get a superuser for the organizer field
        User = get_user_model()
        organizer = User.objects.filter(is_superuser=True).first()
        
        if not organizer:
            self.stdout.write(self.style.ERROR('No superuser found. Please create a superuser first.'))
            return
        
        # Create test tournament with future dates
        start_date = timezone.now() + timedelta(days=7)  # 7 days from now
        end_date = start_date + timedelta(days=2)  # 2 days duration
        registration_deadline = timezone.now() + timedelta(days=5)  # 5 days from now
        
        # Delete any existing test tournament
        TournamentCompetition.objects.filter(name='Test Soccer Tournament 2024').delete()
        
        tournament = TournamentCompetition.objects.create(
            name='Test Soccer Tournament 2024',
            description='A test tournament for registration and camera verification testing',
            sport_code=soccer,
            tournament_type='ROUND_ROBIN',
            start_date=start_date,
            end_date=end_date,
            location='Test Sports Complex, Johannesburg',
            venue_address='123 Test Street, Johannesburg, 2000',
            max_teams=8,
            max_players_per_team=15,
            min_players_per_team=7,
            pool_size=4,
            teams_advance_from_pool=2,
            registration_deadline=registration_deadline,
            registration_fee=0.00,
            is_registration_open=True,  # This is the key setting
            is_active=True,
            is_published=True,  # This is the key setting
            organizer=organizer
        )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created tournament: {tournament.name}'))
        self.stdout.write(f'  - Start Date: {tournament.start_date}')
        self.stdout.write(f'  - Registration Deadline: {tournament.registration_deadline}')
        self.stdout.write(f'  - Location: {tournament.location}')
        self.stdout.write(f'  - Sport: {tournament.sport_code.name}')
        self.stdout.write(f'  - Is Published: {tournament.is_published}')
        self.stdout.write(f'  - Registration Open: {tournament.is_registration_open}')
        self.stdout.write(f'  - Registration URL: /tournaments/register/{tournament.id}/')
        
        self.stdout.write(self.style.SUCCESS('Test tournament setup complete!'))
        self.stdout.write('Now visit: http://localhost:8000/tournaments/')



