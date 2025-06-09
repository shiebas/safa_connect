from django.core.management.base import BaseCommand
from django.db import transaction
from competitions.models import Competition, CompetitionTeam, Fixture

class Command(BaseCommand):
    help = 'Update league table from fixture results'
    
    def add_arguments(self, parser):
        parser.add_argument('competition_id', type=str, help='Competition UUID')
        parser.add_argument('--reset', action='store_true', help='Reset all stats before recalculating')
    
    def handle(self, *args, **options):
        try:
            competition = Competition.objects.get(id=options['competition_id'])
            reset_stats = options['reset']
            
            self.stdout.write(f'📊 Updating league table for: {competition.name}')
            
            with transaction.atomic():
                # Reset stats if requested
                if reset_stats:
                    competition.teams.update(
                        played=0, won=0, drawn=0, lost=0,
                        goals_for=0, goals_against=0, points=0
                    )
                    self.stdout.write('🔄 Reset all team statistics')
                
                # Get all completed fixtures
                completed_fixtures = competition.fixtures.filter(
                    status='completed',
                    home_score__isnull=False,
                    away_score__isnull=False
                )
                
                self.stdout.write(f'🔍 Processing {completed_fixtures.count()} completed fixtures...')
                
                # Process each fixture
                for fixture in completed_fixtures:
                    home_team = fixture.home_team
                    away_team = fixture.away_team
                    home_score = fixture.home_score
                    away_score = fixture.away_score
                    
                    # Update goals
                    home_team.goals_for += home_score
                    home_team.goals_against += away_score
                    away_team.goals_for += away_score
                    away_team.goals_against += home_score
                    
                    # Update matches played
                    home_team.played += 1
                    away_team.played += 1
                    
                    # Determine result and update points
                    if home_score > away_score:
                        # Home win
                        home_team.won += 1
                        home_team.points += competition.points_win
                        away_team.lost += 1
                        away_team.points += competition.points_loss
                        result = f'{fixture.home_team.team.short_name or fixture.home_team.team.name} win'
                    elif away_score > home_score:
                        # Away win
                        away_team.won += 1
                        away_team.points += competition.points_win
                        home_team.lost += 1
                        home_team.points += competition.points_loss
                        result = f'{fixture.away_team.team.short_name or fixture.away_team.team.name} win'
                    else:
                        # Draw
                        home_team.drawn += 1
                        home_team.points += competition.points_draw
                        away_team.drawn += 1
                        away_team.points += competition.points_draw
                        result = 'Draw'
                    
                    # Save team stats
                    home_team.save()
                    away_team.save()
                    
                    self.stdout.write(f'  ✅ {fixture} - {result}')
                
                # Display updated league table
                self.stdout.write('\n📋 Updated League Table:')
                self.stdout.write('─' * 80)
                self.stdout.write(f'{"Pos":<3} {"Team":<25} {"P":<2} {"W":<2} {"D":<2} {"L":<2} {"GF":<3} {"GA":<3} {"GD":<4} {"Pts":<3}')
                self.stdout.write('─' * 80)
                
                # Get teams ordered by league position
                teams = competition.teams.all().order_by('-points', '-goals_for', 'goals_against')
                
                for i, team in enumerate(teams, 1):
                    gd = team.goal_difference
                    gd_str = f'+{gd}' if gd > 0 else str(gd)
                    
                    self.stdout.write(
                        f'{i:<3} {team.team.name[:24]:<25} '
                        f'{team.played:<2} {team.won:<2} {team.drawn:<2} {team.lost:<2} '
                        f'{team.goals_for:<3} {team.goals_against:<3} {gd_str:<4} {team.points:<3}'
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n🏆 League table updated successfully!\n'
                        f'   Processed: {completed_fixtures.count()} fixtures\n'
                        f'   Leader: {teams.first().team.name if teams else "No teams"}'
                    )
                )
                
        except Competition.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ Competition not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
