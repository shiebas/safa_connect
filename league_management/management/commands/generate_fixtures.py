import math
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from league_management.models import Competition, CompetitionTeam, Match, CompetitionGroup

class Command(BaseCommand):
    help = 'Generates round-robin fixtures for a given competition or competition group.'

    def add_arguments(self, parser):
        parser.add_argument('competition_id', type=str, help='The UUID of the Competition to generate fixtures for.')
        parser.add_argument('--group_id', type=str, help='Optional: The UUID of a specific CompetitionGroup within the Competition.')
        parser.add_argument('--clear_existing', action='store_true', help='Clear existing matches for the competition/group before generating new ones.')

    def handle(self, *args, **options):
        competition_id = options['competition_id']
        group_id = options['group_id']
        clear_existing = options['clear_existing']

        try:
            competition = Competition.objects.get(id=competition_id)
        except Competition.DoesNotExist:
            raise CommandError(f'Competition with ID "{competition_id}" does not exist.')

        if group_id:
            try:
                group = CompetitionGroup.objects.get(id=group_id, competition=competition)
                teams_queryset = CompetitionTeam.objects.filter(competition=competition, group=group)
                self.stdout.write(f'Generating fixtures for group "{group.name}" in competition "{competition.name}"...')
            except CompetitionGroup.DoesNotExist:
                raise CommandError(f'Group with ID "{group_id}" does not exist for Competition "{competition.name}".')
        else:
            group = None
            teams_queryset = CompetitionTeam.objects.filter(competition=competition, group__isnull=True) if not competition.has_groups else CompetitionTeam.objects.filter(competition=competition)
            self.stdout.write(f'Generating fixtures for competition "{competition.name}" (all teams)...')

        teams = list(teams_queryset.order_by('team__name'))

        if not teams:
            self.stdout.write(self.style.WARNING('No teams found for the specified competition/group. No fixtures generated.'))
            return

        if clear_existing:
            with transaction.atomic():
                if group:
                    Match.objects.filter(competition=competition, group=group).delete()
                    self.stdout.write(self.style.WARNING(f'Cleared existing matches for group "{group.name}".'))
                else:
                    Match.objects.filter(competition=competition).delete()
                    self.stdout.write(self.style.WARNING(f'Cleared existing matches for competition "{competition.name}".'))

        self._generate_round_robin_fixtures(competition, group, teams)

        self.stdout.write(self.style.SUCCESS('Successfully generated fixtures.'))

    def _generate_round_robin_fixtures(self, competition, group, teams):
        n = len(teams)
        fixtures = []

        if n % 2 != 0:
            # Add a dummy team for odd number of teams
            teams.append(None)
            n += 1

        # Generate rounds
        for r in range(n - 1):
            round_matches = []
            for i in range(n // 2):
                home_team = teams[i]
                away_team = teams[n - 1 - i]

                if home_team and away_team: # Exclude matches with dummy team
                    round_matches.append((home_team, away_team))
            fixtures.append(round_matches)

            # Rotate teams (keep the first team fixed)
            first_team = teams[0]
            rest_of_teams = teams[1:]
            rotated_teams = rest_of_teams[-1:] + rest_of_teams[:-1]
            teams = [first_team] + rotated_teams

        # Create Match objects
        with transaction.atomic():
            match_count = 0
            for round_num, round_matches in enumerate(fixtures):
                for home_team, away_team in round_matches:
                    # Create match (match_date and kickoff_time will be set later)
                    Match.objects.create(
                        competition=competition,
                        group=group,
                        home_team=home_team,
                        away_team=away_team,
                        round_number=round_num + 1,
                        match_day=round_num + 1, # For simplicity, match_day is same as round_number initially
                        match_date='2000-01-01', # Placeholder date
                        kickoff_time='00:00:00', # Placeholder time
                        status='scheduled'
                    )
                    match_count += 1
            self.stdout.write(self.style.SUCCESS(f'Created {match_count} matches.'))
