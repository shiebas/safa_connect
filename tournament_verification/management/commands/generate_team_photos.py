from django.core.management.base import BaseCommand
from tournament_verification.tournament_models import TournamentTeam
from tournament_verification.team_photo_generator import team_photo_generator

class Command(BaseCommand):
    help = 'Generate composite team photos from player registrations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--team-id',
            type=str,
            help='Generate photo for specific team ID only',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration even if team photo already exists',
        )

    def handle(self, *args, **options):
        self.stdout.write('Generating team photos...')
        
        # Get teams to process
        if options['team_id']:
            try:
                teams = [TournamentTeam.objects.get(id=options['team_id'])]
                self.stdout.write(f'Processing specific team: {teams[0].name}')
            except TournamentTeam.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Team with ID {options["team_id"]} not found'))
                return
        else:
            teams = TournamentTeam.objects.all()
            self.stdout.write(f'Processing {teams.count()} teams')
        
        # Process each team
        success_count = 0
        for team in teams:
            self.stdout.write(f'Processing team: {team.name}')
            
            # Skip if team photo already exists and not forcing
            if team.team_photo and not options['force']:
                self.stdout.write(f'  Skipping - team photo already exists')
                continue
            
            # Generate team photo
            try:
                if team.generate_team_photo():
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Generated team photo for {team.name}'))
                    success_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f'  ⚠ Failed to generate team photo for {team.name}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error generating team photo for {team.name}: {e}'))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated {success_count} team photos!'
            )
        )
        
        # Show summary
        total_teams = TournamentTeam.objects.count()
        teams_with_photos = TournamentTeam.objects.filter(team_photo__isnull=False).count()
        self.stdout.write(f'Total teams: {total_teams}')
        self.stdout.write(f'Teams with photos: {teams_with_photos}')
        self.stdout.write(f'Teams without photos: {total_teams - teams_with_photos}')


