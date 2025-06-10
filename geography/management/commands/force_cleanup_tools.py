from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission

class Command(BaseCommand):
    help = 'Force remove SAFA Tools from admin completely'
    
    def handle(self, *args, **options):
        self.stdout.write('🔥 Force removing SAFA Tools from admin...')
        
        try:
            with transaction.atomic():
                # Delete all content types for tools app
                tools_content_types = ContentType.objects.filter(app_label='tools')
                count = tools_content_types.count()
                tools_content_types.delete()
                self.stdout.write(f'🗑️  Deleted {count} content types for tools app')
                
                # Delete all permissions for tools app
                tools_permissions = Permission.objects.filter(content_type__app_label='tools')
                perm_count = tools_permissions.count()
                tools_permissions.delete()
                self.stdout.write(f'🗑️  Deleted {perm_count} permissions for tools app')
                
                # Check and remove tools tables from database
                with connection.cursor() as cursor:
                    # Get all tables starting with tools_
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'tools_%';")
                    tools_tables = cursor.fetchall()
                    
                    for table in tools_tables:
                        table_name = table[0]
                        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
                        self.stdout.write(f'🗑️  Dropped table: {table_name}')
                    
                    # Also check django_migrations table
                    cursor.execute("DELETE FROM django_migrations WHERE app = 'tools';")
                    self.stdout.write('🗑️  Removed tools migration records')
                
                self.stdout.write(
                    self.style.SUCCESS(
                        '✅ SAFA Tools completely removed!\n'
                        'Please restart Django server and clear browser cache.'
                    )
                )
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
