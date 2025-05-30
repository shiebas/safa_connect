from django.core.management import call_command
import os
import sys

def backup_data():
    # Define apps in order of dependencies
    apps_to_backup = [
        ('contenttypes', 'contenttypes'),
        ('auth.user', 'auth_users'),
        ('accounts', 'accounts'),
        ('geography', 'geography'),
        ('membership', 'membership')
    ]
    
    # Create fixtures directory
    os.makedirs('fixtures', exist_ok=True)
    
    for app, name in apps_to_backup:
        filename = f'fixtures/{name}_data.json'
        print(f"\nBacking up {app} to {filename}")
        
        try:
            call_command(
                'dumpdata',
                app,
                indent=2,
                output=filename,
                exclude=['auth.permission', 'contenttypes.contenttype'],
                natural_foreign=True,
                verbosity=2
            )
            print(f"✓ Successfully backed up {app}")
        except Exception as e:
            print(f"✗ Error backing up {app}: {str(e)}", file=sys.stderr)

if __name__ == '__main__':
    print("Starting backup process...")
    backup_data()
    print("\nBackup process completed!")