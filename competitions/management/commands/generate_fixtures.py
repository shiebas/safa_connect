from django.core.management.base import BaseCommand
from django.db import transaction
from competitions.models import Competition, CompetitionTeam, Fixture
from datetime import datetime, timedelta
import itertools

class Command(BaseCommand):
    help = 'Generate fixtures for a competition'
    
    def add_arguments(self, parser):
        parser.add_argument('competition_id', type=str, help='Competition UUID')
        parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)', required=True)
        parser.add_argument('--match-days', type=str, help='Match days (e.g., "saturday,sunday")', default='saturday')
        parser.add_argument('--kickoff-time', type=str, help='Default kickoff time (HH:MM)', default='15:00')
    
    def handle(self, *args, **options):
        try:
            competition = Competition.objects.get(id=options['competition_id'])
            start_date = datetime.strptime(options['start_date'], '%Y-%m-%d').date()
            match_days = [day.strip().lower() for day in options['match_days'].split(',')]
            kickoff_time = datetime.strptime(options['kickoff_time'], '%H:%M').time()
            
            self.stdout.write(f'🏆 Generating fixtures for: {competition.name}')
            
            # Get registered teams
            teams = list(competition.teams.all())
            team_count = len(teams)
            
            if team_count < 2:
                self.stdout.write(self.style.ERROR('❌ Need at least 2 teams to generate fixtures'))
                return
            
            self.stdout.write(f'📋 Teams registered: {team_count}')
            
            with transaction.atomic():
                # Clear existing fixtures
                existing_fixtures = competition.fixtures.count()
                if existing_fixtures > 0:
                    competition.fixtures.all().delete()
                    self.stdout.write(f'🗑️  Deleted {existing_fixtures} existing fixtures')
                
                # Generate round-robin fixtures
                fixtures_created = 0
                current_date = start_date
                
                # Create all possible team combinations
                if competition.rounds == 1:
                    # Single round-robin
                    combinations = list(itertools.combinations(teams, 2))
                else:
                    # Double round-robin (home and away)
                    combinations = []
                    for team1, team2 in itertools.combinations(teams, 2):
                        combinations.append((team1, team2))  # First leg
                        combinations.append((team2, team1))  # Return leg
                
                total_matches = len(combinations)
                self.stdout.write(f'📅 Total matches to schedule: {total_matches}')
                
                # Schedule fixtures
                match_day = 1
                for i, (home, away) in enumerate(combinations):
                    # Find next available match day
                    while current_date.strftime('%A').lower() not in match_days:
                        current_date += timedelta(days=1)
                    
                    # Create fixture
                    fixture = Fixture.objects.create(
                        competition=competition,
                        home_team=home,
                        away_team=away,
                        round_number=1 if competition.rounds == 1 else (1 if i < total_matches // 2 else 2),
                        match_day=match_day,
                        scheduled_date=datetime.combine(current_date, kickoff_time),
                        kickoff_time=kickoff_time,
                        venue=home.team.home_ground or f'{home.team.name} Ground'
                    )
                    
                    fixtures_created += 1
                    
                    # Move to next week for next match
                    if fixtures_created % (team_count // 2) == 0:  # All matches for this round
                        match_day += 1
                        current_date += timedelta(days=7)  # Next week
                    
                    self.stdout.write(f'  ✅ {fixture}')
                
                # Mark fixtures as generated
                competition.fixtures_generated = True
                competition.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n🎉 Fixture generation complete!\n'
                        f'   Competition: {competition.name}\n'
                        f'   Fixtures created: {fixtures_created}\n'
                        f'   Match days: {total_matches // (team_count // 2) if team_count > 1 else 1}\n'
                        f'   Season ends approximately: {current_date}'
                    )
                )
                
        except Competition.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ Competition not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
