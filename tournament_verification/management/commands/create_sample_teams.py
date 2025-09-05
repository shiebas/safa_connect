from django.core.management.base import BaseCommand
from django.utils import timezone
from tournament_verification.tournament_models import TournamentCompetition, TournamentTeam, SportCode
import uuid
from datetime import timedelta

class Command(BaseCommand):
    help = 'Create sample teams for tournaments with team pictures'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample teams...')
        
        # Get or create sport codes
        soccer, created = SportCode.objects.get_or_create(
            code='SOCCER',
            defaults={
                'name': 'Soccer/Football',
                'description': 'Association Football',
                'players_per_team': 11,
                'match_duration_minutes': 90,
                'has_extra_time': True,
                'has_penalties': True,
                'points_for_win': 3,
                'points_for_draw': 1,
                'points_for_loss': 0,
            }
        )
        
        rugby, created = SportCode.objects.get_or_create(
            code='RUGBY',
            defaults={
                'name': 'Rugby',
                'description': 'Rugby Union',
                'players_per_team': 15,
                'match_duration_minutes': 80,
                'has_extra_time': True,
                'has_penalties': True,
                'points_for_win': 4,
                'points_for_draw': 2,
                'points_for_loss': 0,
            }
        )
        
        # Get existing tournaments
        tournaments = TournamentCompetition.objects.filter(is_active=True)
        
        if not tournaments.exists():
            self.stdout.write(self.style.WARNING('No active tournaments found. Please create tournaments first.'))
            return
        
        # Sample team data
        soccer_teams = [
            {
                'name': 'Thunder FC',
                'short_name': 'THU',
                'team_color_primary': '#FF6B35',
                'team_color_secondary': '#F7931E',
                'captain_name': 'John Smith',
                'captain_phone': '+27123456789',
                'captain_email': 'john.thunder@example.com',
            },
            {
                'name': 'Lightning United',
                'short_name': 'LIG',
                'team_color_primary': '#4A90E2',
                'team_color_secondary': '#7ED321',
                'captain_name': 'Mike Johnson',
                'captain_phone': '+27123456790',
                'captain_email': 'mike.lightning@example.com',
            },
            {
                'name': 'Storm Rovers',
                'short_name': 'STR',
                'team_color_primary': '#9013FE',
                'team_color_secondary': '#50E3C2',
                'captain_name': 'David Brown',
                'captain_phone': '+27123456791',
                'captain_email': 'david.storm@example.com',
            },
            {
                'name': 'Eagle Warriors',
                'short_name': 'EAG',
                'team_color_primary': '#BD10E0',
                'team_color_secondary': '#B8E986',
                'captain_name': 'Chris Wilson',
                'captain_phone': '+27123456792',
                'captain_email': 'chris.eagle@example.com',
            },
            {
                'name': 'Phoenix FC',
                'short_name': 'PHO',
                'team_color_primary': '#F5A623',
                'team_color_secondary': '#D0021B',
                'captain_name': 'Alex Davis',
                'captain_phone': '+27123456793',
                'captain_email': 'alex.phoenix@example.com',
            },
            {
                'name': 'Titan United',
                'short_name': 'TIT',
                'team_color_primary': '#417505',
                'team_color_secondary': '#7ED321',
                'captain_name': 'Ryan Miller',
                'captain_phone': '+27123456794',
                'captain_email': 'ryan.titan@example.com',
            }
        ]
        
        rugby_teams = [
            {
                'name': 'Lions Rugby Club',
                'short_name': 'LIO',
                'team_color_primary': '#FFD700',
                'team_color_secondary': '#000000',
                'captain_name': 'James Anderson',
                'captain_phone': '+27123456795',
                'captain_email': 'james.lions@example.com',
            },
            {
                'name': 'Sharks RFC',
                'short_name': 'SHA',
                'team_color_primary': '#000080',
                'team_color_secondary': '#FFFFFF',
                'captain_name': 'Tom Taylor',
                'captain_phone': '+27123456796',
                'captain_email': 'tom.sharks@example.com',
            },
            {
                'name': 'Bulls Rugby',
                'short_name': 'BUL',
                'team_color_primary': '#FF4500',
                'team_color_secondary': '#FFFFFF',
                'captain_name': 'Ben White',
                'captain_phone': '+27123456797',
                'captain_email': 'ben.bulls@example.com',
            },
            {
                'name': 'Stormers RFC',
                'short_name': 'STO',
                'team_color_primary': '#0000FF',
                'team_color_secondary': '#FFFFFF',
                'captain_name': 'Sam Green',
                'captain_phone': '+27123456798',
                'captain_email': 'sam.stormers@example.com',
            }
        ]
        
        # Create teams for each tournament
        for tournament in tournaments:
            self.stdout.write(f'Creating teams for tournament: {tournament.name}')
            
            # Clear existing teams
            tournament.teams.all().delete()
            
            # Choose team data based on sport
            if tournament.sport_code.code == 'SOCCER':
                team_data = soccer_teams
            elif tournament.sport_code.code == 'RUGBY':
                team_data = rugby_teams
            else:
                team_data = soccer_teams  # Default to soccer teams
            
            # Create teams
            for i, team_info in enumerate(team_data[:tournament.max_teams]):
                team = TournamentTeam.objects.create(
                    tournament=tournament,
                    name=team_info['name'],
                    short_name=team_info['short_name'],
                    team_color_primary=team_info['team_color_primary'],
                    team_color_secondary=team_info['team_color_secondary'],
                    captain_name=team_info['captain_name'],
                    captain_phone=team_info['captain_phone'],
                    captain_email=team_info['captain_email'],
                    is_confirmed=True
                )
                
                self.stdout.write(f'  Created team: {team.name} ({team.short_name})')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created teams for {tournaments.count()} tournaments!'
            )
        )
        
        # Display summary
        total_teams = TournamentTeam.objects.count()
        self.stdout.write(f'Total teams in system: {total_teams}')
        
        for tournament in tournaments:
            team_count = tournament.teams.count()
            self.stdout.write(f'{tournament.name}: {team_count} teams')


