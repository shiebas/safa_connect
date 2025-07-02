#!/usr/bin/env python
"""
Script to fix all import statements for Invoice models
"""
import os
import re

# Files that need fixing
files_to_fix = [
    'safa_global/dashboard_views.py',
    'supporters/views.py', 
    'events/views.py',
    'membership/management/commands/update_invoice_status.py',
    'membership/invoice_views.py'
]

# Pattern to replace
old_pattern = r'from membership\.models\.invoice import'
new_pattern = 'from membership.invoice_models import'

for file_path in files_to_fix:
    if os.path.exists(file_path):
        print(f"Fixing {file_path}...")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the import
        new_content = re.sub(old_pattern, new_pattern, content)
        
        if content != new_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✓ Fixed imports in {file_path}")
        else:
            print(f"- No changes needed in {file_path}")
    else:
        print(f"! File not found: {file_path}")

print("\n🎉 Import fixing complete!")
