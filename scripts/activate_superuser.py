import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_connect.settings')
django.setup()

from accounts.models import CustomUser

def activate_superusers():
    """
    Finds all superusers and activates them if they are inactive.
    """
    superusers = CustomUser.objects.filter(is_superuser=True)
    if superusers.exists():
        for su in superusers:
            if not su.is_active:
                su.is_active = True
                su.save()
                print(f"Superuser {su.email} has been activated.")
            else:
                print(f"Superuser {su.email} is already active.")
    else:
        print("No superusers found.")

if __name__ == "__main__":
    activate_superusers()
