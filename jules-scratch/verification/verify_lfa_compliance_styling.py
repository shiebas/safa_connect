import sys
import os
from playwright.sync_api import sync_playwright
from django.core.management import call_command

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def run():
    # Setup Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_connect.settings')
    import django
    django.setup()

    # Run migrations
    call_command('migrate')

    from django.contrib.auth import get_user_model
    from geography.models import Country, NationalFederation, Province, Region, LocalFootballAssociation

    User = get_user_model()

    # Create test data
    country, _ = Country.objects.get_or_create(name='South Africa')
    national_federation, _ = NationalFederation.objects.get_or_create(name='SAFA', country=country)
    province, _ = Province.objects.get_or_create(name='Test Province', national_federation=national_federation)
    region, _ = Region.objects.get_or_create(name='Test Region', province=province)
    lfa, _ = LocalFootballAssociation.objects.get_or_create(name='Test LFA', region=region)
    user, created = User.objects.get_or_create(
        email='lfa_admin@test.com',
        defaults={
            'first_name': 'LFA',
            'last_name': 'Admin',
            'role': 'ADMIN_LOCAL_FED',
            'local_federation': lfa,
        }
    )
    if created:
        user.set_password('password')
        user.save()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Login
        page.goto("http://localhost:8000/local-accounts/login/")
        page.fill('input[name="login"]', 'lfa_admin@test.com')
        page.fill('input[name="password"]', 'password')
        page.click('button[type="submit"]')

        # Navigate to the LFA compliance page
        page.goto("http://localhost:8000/local-accounts/lfa-compliance/")

        # Take a screenshot
        page.screenshot(path="jules-scratch/verification/verification.png")

        browser.close()

if __name__ == "__main__":
    run()
