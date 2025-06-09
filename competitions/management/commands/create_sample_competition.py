from django.core.management.base import BaseCommand
from django.db import transaction
from competitions.models import Competition, Team, CompetitionTeam
from geography.models import Region, LocalFootballAssociation
from datetime import date, datetime

class Command(BaseCommand):
    help = 'Create a sample Regional Mens League with teams'
    
    def add_arguments(self, parser):
        parser.add_argument('--region-id', type=int, help='Region ID (1-52)', default=1)
        parser.add_argument('--teams', type=int, help='Number of teams to create', default=8)
    
    def handle(self, *args, **options):
        region_id = options['region_id']
        team_count = options['teams']
        
        try:
            region = Region.objects.get(id=region_id)
            lfas = list(region.localfootballassociation_set.all())
            
            if len(lfas) < team_count:
                self.stdout.write(self.style.WARNING(f'⚠️  Only {len(lfas)} LFAs available in {region.name}'))
                team_count = len(lfas)
            
            self.stdout.write(f'🏆 Creating sample competition for {region.name}...')
            
            with transaction.atomic():
                # Create competition
                competition = Competition.objects.create(
                    name=f'{region.name} Regional Mens League',
                    short_name=f'{region.name} RML',
                    competition_type='league',
                    level='regional',
                    region=region,
                    season_year='2024/2025',
                    start_date=date(2024, 8, 1),
                    end_date=date(2025, 5, 31),
                    sponsor_name='SAFA Development Fund',
                    max_teams=16,
                    rounds=2  # Double round-robin
                )
                
                self.stdout.write(f'✅ Created competition: {competition.name}')
                
                # Create sample teams
                team_names = [
                    'United FC', 'City FC', 'Rovers FC', 'Athletic FC',
                    'Wanderers FC', 'Rangers FC', 'Dynamos FC', 'Chiefs FC',
                    'Pirates FC', 'Celtic FC', 'Arsenal FC', 'Liverpool FC',
                    'Barcelona FC', 'Real FC', 'Milan FC', 'Bayern FC'
                ]
                
                created_teams = []
                for i in range(team_count):
                    lfa = lfas[i % len(lfas)]
                    team_name = f'{region.name} {team_names[i]}'
                    
                    # Create team
                    team = Team.objects.create(
                        name=team_name,
                        short_name=team_names[i],
                        lfa=lfa,
                        home_ground=f'{team_names[i]} Stadium',
                        manager_name=f'Manager {i+1}',
                        contact_phone=f'083{i+1:03d}0000',
                        contact_email=f'manager{i+1}@{team_names[i].lower().replace(" ", "")}.co.za'
                    )
                    
                    # Register team for competition
                    CompetitionTeam.objects.create(
                        competition=competition,
                        team=team,
                        registration_fee_paid=True
                    )
                    
                    created_teams.append(team)
                    self.stdout.write(f'  ✅ {team.name} ({lfa.name})')
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n🎉 Sample competition created!\n'
                        f'   Competition: {competition.name}\n'
                        f'   Teams: {len(created_teams)}\n'
                        f'   Competition ID: {competition.id}\n\n'
                        f'Next steps:\n'
                        f'1. Generate fixtures: python manage.py generate_fixtures {competition.id} --start-date 2024-08-10\n'
                        f'2. Add some results manually in admin\n'
                        f'3. Update league table: python manage.py update_league_table {competition.id}'
                    )
                )
                
        except Region.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Region with ID {region_id} not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
