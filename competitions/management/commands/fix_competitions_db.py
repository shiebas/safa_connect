from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Check and fix competitions database structure'
    
    def handle(self, *args, **options):
        self.stdout.write('🔍 Checking competitions database structure...')
        
        with connection.cursor() as cursor:
            try:
                # Check if competitions table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='competitions_competition';")
                table_exists = cursor.fetchone()
                
                if not table_exists:
                    self.stdout.write(self.style.WARNING('⚠️  Competitions table does not exist'))
                    self.stdout.write('Run: python manage.py makemigrations competitions')
                    self.stdout.write('Then: python manage.py migrate')
                    return
                
                # Check table structure
                cursor.execute("PRAGMA table_info(competitions_competition);")
                columns = cursor.fetchall()
                
                self.stdout.write('📋 Current table columns:')
                for col in columns:
                    self.stdout.write(f'  - {col[1]} ({col[2]})')
                
                # Check for missing columns
                column_names = [col[1] for col in columns]
                expected_columns = ['id', 'safa_id', 'name', 'season_year', 'competition_type']
                
                missing = [col for col in expected_columns if col not in column_names]
                if missing:
                    self.stdout.write(self.style.ERROR(f'❌ Missing columns: {missing}'))
                    self.stdout.write('Need to recreate migrations')
                else:
                    self.stdout.write(self.style.SUCCESS('✅ All expected columns present'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Database error: {str(e)}'))
