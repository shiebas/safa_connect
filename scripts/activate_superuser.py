from accounts.models import CustomUser

# IMPORTANT: Replace 'your_superuser_email@example.com' with the actual email of your superuser account.
# If you haven't created a superuser yet, please run 'python manage.py createsuperuser' first.

superuser_email = 'admin@example.com' # <--- CHANGE THIS TO YOUR SUPERUSER'S EMAIL

try:
    user = CustomUser.objects.get(email=superuser_email)
    user.is_active = True
    user.is_approved = True
    user.save()
    print(f"Superuser '{user.email}' has been activated (is_active=True, is_approved=True).")
except CustomUser.DoesNotExist:
    print(f"Error: Superuser with email '{superuser_email}' not found. Please ensure the email is correct and the superuser account exists.")
except Exception as e:
    print(f"An error occurred: {e}")
