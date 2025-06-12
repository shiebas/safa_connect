"""
This file is used to test imports without having to run Django.
This will help us identify import path issues.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

print("Python path:", sys.path)

print("\nChecking if the models.py file exists")
if os.path.exists('membership/models.py'):
    print("✓ models.py exists")
else:
    print("✗ models.py does not exist")

print("\nChecking if models/__init__.py exists")
if os.path.exists('membership/models/__init__.py'):
    print("✓ models/__init__.py exists")
else:
    print("✗ models/__init__.py does not exist")

print("\nChecking if models/main.py symlink exists")
if os.path.exists('membership/models/main.py'):
    print("✓ models/main.py symlink exists")
else:
    print("✗ models/main.py does not exist")

print("\nTrying to import membership module")
try:
    import membership
    print("✓ Successfully imported membership")
except ImportError as e:
    print(f"✗ Failed to import membership: {e}")

print("\nTrying to import membership.models module")
try:
    import membership.models
    print("✓ Successfully imported membership.models module")
    print(f"membership.models.__file__ = {membership.models.__file__}")
except ImportError as e:
    print(f"✗ Failed to import membership.models: {e}")

print("\nTrying to import membership.models.main module")
try:
    import membership.models.main
    print("✓ Successfully imported membership.models.main module")
    print(f"membership.models.main.__file__ = {membership.models.main.__file__}")
except ImportError as e:
    print(f"✗ Failed to import membership.models.main: {e}")

print("\nTrying to import Member from membership.models.main")
try:
    from membership.models.main import Member
    print("✓ Successfully imported Member class from main")
except ImportError as e:
    print(f"✗ Failed to import Member from main: {e}")

print("\nTrying to import Member from membership.models")
try:
    from membership.models import Member
    print("✓ Successfully imported Member class")
except ImportError as e:
    print(f"✗ Failed to import Member: {e}")

print("\nTrying to import Invoice from membership.models.invoice")
try:
    from membership.models.invoice import Invoice
    print("✓ Successfully imported Invoice class")
except ImportError as e:
    print(f"✗ Failed to import Invoice: {e}")
