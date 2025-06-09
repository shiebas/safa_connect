from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps

class Command(BaseCommand):
    help = 'Check existing competition models and structure'
    
    def handle(self, *args, **options):
        self.stdout.write('🔍 Analyzing existing competition structure...')
        
        # Check what models already exist
        try:
            all_models = apps.get_app_config('competitions').get_models()
            self.stdout.write(f'📋 Found {len(all_models)} existing models:')
            for model in all_models:
                self.stdout.write(f'  - {model.__name__}')
        except:
            self.stdout.write('⚠️  No competitions app models found')
        
        # Check database tables
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'competitions_%';")
            tables = cursor.fetchall()
            
            self.stdout.write(f'\n📊 Existing competition tables ({len(tables)}):')
            for table in tables:
                table_name = table[0]
                self.stdout.write(f'\n🔍 {table_name}:')
                
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                for col in columns:
                    self.stdout.write(f'  - {col[1]} ({col[2]})')
        
        # Check related models that might exist
        related_tables = ['geography_', 'accounts_', 'membership_']
        for prefix in related_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '{prefix}%';")
            tables = cursor.fetchall()
            if tables:
                self.stdout.write(f'\n📋 Related {prefix} tables:')
                for table in tables:
                    self.stdout.write(f'  - {table[0]}')
        
        self.stdout.write(
            '\n🔧 Next steps:\n'
            '1. I can adapt to your existing structure\n'
            '2. Or we can create a new competitions app name\n'
            '3. Tell me what fields/relationships you need'
        )
