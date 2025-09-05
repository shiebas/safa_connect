from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from tournament_verification.tournament_models import (
    TournamentCompetition, SportCode, TournamentTeam, TournamentPlayer, 
    TournamentTeamPlayer, TournamentPool
)
from tournament_verification.fixture_generator import FixtureGenerator

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample tournaments with teams and players for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sport',
            type=str,
            choices=['SOCCER', 'RUGBY', 'BASKETBALL', 'TENNIS', 'CRICKET'],
            default='SOCCER',
            help='Sport code for the tournament'
        )
        parser.add_argument(
            '--teams',
            type=int,
            default=8,
            help='Number of teams to create'
        )
        parser.add_argument(
            '--players-per-team',
            type=int,
            default=15,
            help='Number of players per team'
        )

    def handle(self, *args, **options):
        sport_code = options['sport']
        num_teams = options['teams']
        players_per_team = options['players_per_team']

        # Get or create superuser
        superuser = User.objects.filter(is_superuser=True).first()
        if not superuser:
            self.stdout.write(
                self.style.ERROR('No superuser found. Please create a superuser first.')
            )
            return

        # Get sport code
        try:
            sport = SportCode.objects.get(code=sport_code)
        except SportCode.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Sport code {sport_code} not found. Run setup_sport_codes first.')
            )
            return

        # Create tournament
        start_date = timezone.now() + timedelta(days=30)
        end_date = start_date + timedelta(days=3)
        registration_deadline = start_date - timedelta(days=7)

        tournament = TournamentCompetition.objects.create(
            name=f'{sport.name} Championship 2024',
            description=f'A competitive {sport.name.lower()} tournament featuring top teams.',
            sport_code=sport,
            tournament_type='POOL_PLAYOFF',
            start_date=start_date,
            end_date=end_date,
            registration_deadline=registration_deadline,
            location='Cape Town Stadium',
            venue_address='Cape Town Stadium, Green Point, Cape Town, 8005',
            max_teams=16,
            max_players_per_team=sport.players_per_team + 5,  # Allow some substitutes
            min_players_per_team=sport.players_per_team,
            pool_size=4,
            teams_advance_from_pool=2,
            registration_fee=0.00,  # Free for tournament players
            is_registration_open=True,
            is_published=True,
            organizer=superuser
        )

        self.stdout.write(
            self.style.SUCCESS(f'Created tournament: {tournament.name}')
        )

        # Create teams
        team_names = self._generate_team_names(sport_code, num_teams)
        teams = []

        for i, team_name in enumerate(team_names):
            team = TournamentTeam.objects.create(
                tournament=tournament,
                name=team_name,
                short_name=team_name.split()[-1][:3].upper(),  # Use last word, first 3 chars
                team_color_primary=self._get_team_color(i, 'primary'),
                team_color_secondary=self._get_team_color(i, 'secondary'),
                captain_name=f'Captain {team_name}',
                captain_phone=f'082{i:03d}0000',
                captain_email=f'captain.{team_name.lower().replace(" ", ".")}@example.com',
                is_confirmed=True
            )
            teams.append(team)
            self.stdout.write(f'Created team: {team.name}')

        # Create pools
        self._create_pools(tournament, teams)

        # Create players and assign to teams
        for team in teams:
            self._create_team_players(team, players_per_team, sport)

        # Generate fixtures
        self._generate_fixtures(tournament)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created tournament with {len(teams)} teams and '
                f'{len(teams) * players_per_team} players'
            )
        )

    def _generate_team_names(self, sport_code, num_teams):
        """Generate realistic team names based on sport"""
        if sport_code == 'SOCCER':
            prefixes = ['FC', 'United', 'City', 'Athletic', 'Rovers', 'Wanderers', 'Town', 'Villa']
            suffixes = ['Lions', 'Eagles', 'Tigers', 'Bears', 'Wolves', 'Sharks', 'Falcons', 'Panthers']
        elif sport_code == 'RUGBY':
            prefixes = ['Rugby', 'Union', 'Club', 'Athletic', 'Rovers', 'Wanderers', 'Town', 'Villa']
            suffixes = ['Lions', 'Eagles', 'Tigers', 'Bears', 'Wolves', 'Sharks', 'Falcons', 'Panthers']
        elif sport_code == 'BASKETBALL':
            prefixes = ['Basketball', 'Hoops', 'Ballers', 'Shooters', 'Dunkers', 'Slam', 'Court', 'Rim']
            suffixes = ['Lions', 'Eagles', 'Tigers', 'Bears', 'Wolves', 'Sharks', 'Falcons', 'Panthers']
        else:
            prefixes = ['Sport', 'Club', 'Team', 'Athletic', 'Rovers', 'Wanderers', 'Town', 'Villa']
            suffixes = ['Lions', 'Eagles', 'Tigers', 'Bears', 'Wolves', 'Sharks', 'Falcons', 'Panthers']

        team_names = []
        for i in range(num_teams):
            prefix = prefixes[i % len(prefixes)]
            suffix = suffixes[i % len(suffixes)]
            team_names.append(f'{prefix} {suffix}')

        return team_names

    def _get_team_color(self, index, color_type):
        """Get team colors based on index"""
        colors = {
            'primary': ['#FF0000', '#0000FF', '#00FF00', '#FFFF00', '#FF00FF', '#00FFFF', '#FFA500', '#800080'],
            'secondary': ['#FFFFFF', '#FFFFFF', '#FFFFFF', '#000000', '#FFFFFF', '#000000', '#000000', '#FFFFFF']
        }
        return colors[color_type][index % len(colors[color_type])]

    def _create_pools(self, tournament, teams):
        """Create pools and assign teams"""
        pool_size = tournament.pool_size
        num_pools = (len(teams) + pool_size - 1) // pool_size

        for i in range(num_pools):
            pool_name = chr(65 + i)  # A, B, C, etc.
            pool = TournamentPool.objects.create(
                tournament=tournament,
                name=pool_name
            )

            # Assign teams to pool
            start_idx = i * pool_size
            end_idx = min(start_idx + pool_size, len(teams))
            pool_teams = teams[start_idx:end_idx]
            
            for team in pool_teams:
                team.pool = pool_name
                team.save()
                pool.teams.add(team)

            self.stdout.write(f'Created Pool {pool_name} with {len(pool_teams)} teams')

    def _create_team_players(self, team, num_players, sport):
        """Create players for a team"""
        first_names = [
            'John', 'James', 'Michael', 'David', 'Robert', 'William', 'Richard', 'Thomas',
            'Christopher', 'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald', 'Steven',
            'Paul', 'Andrew', 'Joshua', 'Kenneth', 'Kevin', 'Brian', 'George', 'Timothy',
            'Ronald', 'Jason', 'Edward', 'Jeffrey', 'Ryan', 'Jacob', 'Gary', 'Nicholas',
            'Eric', 'Jonathan', 'Stephen', 'Larry', 'Justin', 'Scott', 'Brandon', 'Benjamin'
        ]

        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
            'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
            'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker',
            'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores'
        ]

        positions = self._get_positions_for_sport(sport.code)

        for i in range(num_players):
            first_name = first_names[i % len(first_names)]
            last_name = last_names[i % len(last_names)]
            
            # Create tournament player
            player = TournamentPlayer.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=f'{first_name.lower()}.{last_name.lower()}@example.com',
                phone_number=f'082{i:03d}0000',
                date_of_birth=timezone.now().date() - timedelta(days=365 * (20 + (i % 15))),  # Age 20-35
                gender='M' if i % 2 == 0 else 'F',
                id_number=f'900{i:06d}0000',
                id_document_type='ID',
                emergency_contact_name=f'Emergency Contact {i}',
                emergency_contact_phone=f'082{i:03d}0001',
                emergency_contact_relationship='Parent',
                medical_conditions='None',
                registration_fee=0.00
            )

            # Assign to team
            position = positions[i % len(positions)] if positions else ''
            jersey_number = i + 1
            is_captain = i == 0
            is_vice_captain = i == 1

            TournamentTeamPlayer.objects.create(
                team=team,
                player=player,
                position=position,
                jersey_number=jersey_number,
                is_captain=is_captain,
                is_vice_captain=is_vice_captain
            )

    def _get_positions_for_sport(self, sport_code):
        """Get positions for different sports"""
        positions = {
            'SOCCER': [
                'Goalkeeper', 'Defender', 'Defender', 'Defender', 'Defender',
                'Midfielder', 'Midfielder', 'Midfielder', 'Midfielder',
                'Forward', 'Forward'
            ],
            'RUGBY': [
                'Prop', 'Hooker', 'Prop', 'Lock', 'Lock', 'Flanker', 'Flanker',
                'Number 8', 'Scrum-half', 'Fly-half', 'Wing', 'Centre', 'Centre',
                'Wing', 'Fullback'
            ],
            'BASKETBALL': [
                'Point Guard', 'Shooting Guard', 'Small Forward', 'Power Forward', 'Center'
            ],
            'TENNIS': ['Player'],
            'CRICKET': [
                'Batsman', 'Bowler', 'Wicket-keeper', 'All-rounder'
            ]
        }
        return positions.get(sport_code, ['Player'])

    def _generate_fixtures(self, tournament):
        """Generate fixtures for the tournament"""
        try:
            generator = FixtureGenerator(tournament)
            matches = generator.generate_fixtures()
            
            # Save matches to database
            for match in matches:
                match.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Generated {len(matches)} fixtures for the tournament')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating fixtures: {str(e)}')
            )