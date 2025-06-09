from django.core.management.base import BaseCommand
import os
import py_compile
import sys

class Command(BaseCommand):
    help = 'Check for syntax errors in Python files'
    
    def handle(self, *args, **options):
        self.stdout.write('🔍 Checking for syntax errors...')
        
        # Check main project files
        files_to_check = [
            'safa_global/settings.py',
            'safa_global/urls.py', 
            'safa_global/wsgi.py',
            'accounts/models.py',
            'geography/models.py',
            'membership_cards/models.py',
        ]
        
        errors_found = False
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                try:
                    py_compile.compile(file_path, doraise=True)
                    self.stdout.write(f'✅ {file_path}')
                except py_compile.PyCompileError as e:
                    self.stdout.write(self.style.ERROR(f'❌ {file_path}: {str(e)}'))
                    errors_found = True
            else:
                self.stdout.write(f'⚠️  {file_path} not found')
        
        if not errors_found:
            self.stdout.write(self.style.SUCCESS('✅ No syntax errors found'))
        
        # Try importing the problematic module
        try:
            from safa_global.wsgi import application
            self.stdout.write('✅ WSGI application imports successfully')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ WSGI import error: {str(e)}'))
