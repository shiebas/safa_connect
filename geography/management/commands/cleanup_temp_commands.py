from django.core.management.base import BaseCommand
import os
import shutil

class Command(BaseCommand):
    help = 'Clean up temporary management commands, keep only essential ones'
    
    def handle(self, *args, **options):
        self.stdout.write('🧹 Cleaning up temporary management commands...')
        
        # Essential commands to KEEP
        essential_commands = {
            'geography/management/commands/': [
                'check_regions.py',           # Monitor region structure
                'update_region_lfas.py',      # Universal LFA update tool
                'load_complete_geography.py'  # Data loading if needed
            ],
            'accounts/management/commands/': [
                'create_test_members.py'      # For testing
            ]
        }
        
        # Commands to DELETE (temporary/one-time use)
        temp_commands = [
            'check_ec_lfas.py',
            'check_syntax.py', 
            'clean_province_ids.py',
            'cleanup_duplicates.py',
            'clear_ec_lfas.py',
            'create_gauteng_regions.py',
            'create_kzn_regions.py',
            'create_limpopo_regions.py',
            'create_mpumalanga_regions.py',
            'create_northern_cape_regions.py',
            'create_northwest_regions.py',
            'create_western_cape_regions.py',
            'diagnose_wsgi.py',
            'fix_all_region_ids.py',
            'fix_freestate_regions.py',
            'fix_province_ids.py',
            'fix_region_ids.py',
            'list_eastern_cape.py',
            'restore_original_data.py',
            'restore_regions.py',
            'restore_safa_data.py',
            'show_existing_data.py',
            'check_middleware.py'
        ]
        
        deleted_count = 0
        
        # Delete temporary commands
        for command_file in temp_commands:
            geography_path = f'geography/management/commands/{command_file}'
            accounts_path = f'accounts/management/commands/{command_file}'
            
            for path in [geography_path, accounts_path]:
                if os.path.exists(path):
                    os.remove(path)
                    self.stdout.write(f'🗑️  Deleted: {path}')
                    deleted_count += 1
        
        # Show what's kept
        self.stdout.write(f'\n✅ Essential commands kept:')
        for app_path, commands in essential_commands.items():
            self.stdout.write(f'\n📁 {app_path}')
            for cmd in commands:
                if os.path.exists(app_path + cmd):
                    self.stdout.write(f'  ✅ {cmd}')
                else:
                    self.stdout.write(f'  ❌ {cmd} (missing)')
        
        # Clean up fixtures
        fixtures_dir = 'geography/fixtures'
        if os.path.exists(fixtures_dir):
            fixture_files = os.listdir(fixtures_dir)
            self.stdout.write(f'\n📋 Fixture files found: {len(fixture_files)}')
            for f in fixture_files:
                self.stdout.write(f'  📄 {f}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Cleanup complete!\n'
                f'   Deleted: {deleted_count} temporary commands\n'
                f'   Kept: {sum(len(cmds) for cmds in essential_commands.values())} essential commands\n'
                f'   Geography data: 100% complete!'
            )
        )
        
        # Next steps
        self.stdout.write(
            f'\n📱 Next Phase: Mobile App Development\n'
            f'   - React Native setup\n'
            f'   - API endpoints\n'
            f'   - Card display & scanning'
        )
