from django.core.management.base import BaseCommand
import os
import re

class Command(BaseCommand):
    help = 'Search for "PROV" code generation in the codebase'
    
    def handle(self, *args, **options):
        self.stdout.write('🔍 Searching for "PROV" code generation...')
        
        # Search patterns
        patterns = [
            r'PROV',
            r'province.*code',
            r'region.*code.*upper',
            r'\.name\[:3\]',
        ]
        
        # Directories to search
        search_dirs = [
            'geography',
            'league_management', 
            'membership_cards',
            'accounts',
            'membership',
        ]
        
        found_files = []
        
        for directory in search_dirs:
            if os.path.exists(directory):
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    
                                for pattern in patterns:
                                    matches = re.finditer(pattern, content, re.IGNORECASE)
                                    for match in matches:
                                        line_num = content[:match.start()].count('\n') + 1
                                        line_content = content.split('\n')[line_num - 1].strip()
                                        
                                        self.stdout.write(f'📍 Found in {file_path}:{line_num}')
                                        self.stdout.write(f'   Pattern: {pattern}')
                                        self.stdout.write(f'   Line: {line_content}')
                                        self.stdout.write('')
                                        
                                        if file_path not in found_files:
                                            found_files.append(file_path)
                                            
                            except Exception as e:
                                self.stdout.write(f'❌ Error reading {file_path}: {e}')
        
        if found_files:
            self.stdout.write(f'🎯 Found potential PROV code in {len(found_files)} files:')
            for file_path in found_files:
                self.stdout.write(f'   - {file_path}')
        else:
            self.stdout.write('✅ No PROV code patterns found')
