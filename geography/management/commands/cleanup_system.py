from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Clean up removed apps and fix system issues'
    
    def handle(self, *args, **options):
        self.stdout.write('🧹 Cleaning up system...')
        
        try:
            with connection.cursor() as cursor:
                # Check if tools tables exist and remove them
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'tools_%';")
                tools_tables = cursor.fetchall()
                
                if tools_tables:
                    self.stdout.write(f'Found {len(tools_tables)} tools tables to remove')
                    for table in tools_tables:
                        cursor.execute(f"DROP TABLE IF EXISTS {table[0]};")
                        self.stdout.write(f'  Dropped table: {table[0]}')
                
                # Clean up django_content_type entries
                cursor.execute("DELETE FROM django_content_type WHERE app_label = 'tools';")
                self.stdout.write('Cleaned up content types for tools app')
                
            self.stdout.write(
                self.style.SUCCESS('✅ System cleanup complete!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during cleanup: {str(e)}')
            )
