from django.core.management.base import BaseCommand
from competitions.models import Competition

class Command(BaseCommand):
    help = 'List all competitions with their UUIDs'
    
    def handle(self, *args, **options):
        self.stdout.write('🏆 Available Competitions:')
        self.stdout.write('─' * 80)
        
        competitions = Competition.objects.all().order_by('-season_year', 'name')
        
        if not competitions.exists():
            self.stdout.write('❌ No competitions found. Create one first with:')
            self.stdout.write('   python manage.py create_sample_competition --region-id 1 --teams 8')
            return
        
        for comp in competitions:
            team_count = comp.teams.count()
            fixture_count = comp.fixtures.count()
            
            self.stdout.write(f'📋 {comp.name}')
            self.stdout.write(f'   UUID: {comp.id}')
            self.stdout.write(f'   SAFA ID: {comp.safa_id}')
            self.stdout.write(f'   Type: {comp.get_competition_type_display()} | Level: {comp.get_level_display()}')
            self.stdout.write(f'   Season: {comp.season_year}')
            self.stdout.write(f'   Teams: {team_count} | Fixtures: {fixture_count}')
            self.stdout.write(f'   Status: {"✅ Active" if comp.is_active else "❌ Inactive"}')
            
            if comp.region:
                self.stdout.write(f'   Region: {comp.region.name}')
            if comp.sponsor_name:
                self.stdout.write(f'   Sponsor: {comp.sponsor_name}')
            
            self.stdout.write('')
        
        self.stdout.write('🔧 Commands you can run:')
        if competitions:
            comp = competitions.first()
            self.stdout.write(f'   Generate fixtures: python manage.py generate_fixtures {comp.id} --start-date 2024-08-10')
            self.stdout.write(f'   Update league table: python manage.py update_league_table {comp.id}')
        self.stdout.write('')
