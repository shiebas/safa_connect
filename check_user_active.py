from accounts.models import CustomUser
import sys

if len(sys.argv) < 2:
    print("Usage: python check_user_active.py <email>")
    sys.exit(1)

email = sys.argv[1]

try:
    user = CustomUser.objects.get(email=email)
    print(f"User {user.email} is_active: {user.is_active}")
except CustomUser.DoesNotExist:
    print(f"User with email {email} not found.")
except Exception as e:
    print(f"An error occurred: {e}")