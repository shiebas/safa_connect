from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Clean up admin for removed SAFA Tools app'
    
    def handle(self, *args, **options):
        self.stdout.write('🧹 Cleaning up admin interface...')
        
        try:
            # Remove content types for tools app
            deleted_count = ContentType.objects.filter(app_label='tools').delete()
            self.stdout.write(f'🗑️  Deleted {deleted_count[0]} content types for tools app')
            
            # Check for any remaining tools tables
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'tools_%';")
                tools_tables = cursor.fetchall()
                
                if tools_tables:
                    self.stdout.write(f'Found {len(tools_tables)} tools tables:')
                    for table in tools_tables:
                        try:
                            cursor.execute(f"DROP TABLE IF EXISTS {table[0]};")
                            self.stdout.write(f'  ✅ Dropped: {table[0]}')
                        except Exception as e:
                            self.stdout.write(f'  ❌ Error dropping {table[0]}: {e}')
                else:
                    self.stdout.write('✅ No tools tables found')
            
            # Clear Django's admin cache
            self.stdout.write('🔄 Clearing admin cache...')
            
            self.stdout.write(
                self.style.SUCCESS(
                    '✅ Admin cleanup complete!\n'
                    'Please restart the Django server to see changes.'
                )
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
