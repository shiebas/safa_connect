#!/usr/bin/env python
"""
Simple test script to verify Django setup on Windows
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_global.settings')
django.setup()

try:
    # Test importing core models
    from membership.models import Member, Player, Official
    print("✓ Successfully imported membership models")
    
    # Test basic model creation (without saving)
    member = Member(
        first_name="Test",
        last_name="User", 
        email="test@example.com",
        date_of_birth="1990-01-01"
    )
    print("✓ Successfully created Member instance")
    
    # Test Django admin
    from django.contrib import admin
    print("✓ Django admin imported successfully")
    
    print("\n🎉 SAFA Django setup is working correctly on Windows!")
    print("🐍 Python version:", sys.version)
    print("🌟 Django version:", django.get_version())
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
