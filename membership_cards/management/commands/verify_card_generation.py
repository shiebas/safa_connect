from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from membership_cards.models import DigitalCard, PhysicalCardTemplate
from membership_cards.card_generator import SAFACardGenerator
from django.core.files.images import ImageFile
from django.conf import settings
import os
from datetime import date
from django.test import RequestFactory
from membership_cards.views import export_cards_csv
from membership_cards.card_generator import generate_print_ready_pdf
from membership_cards.models import PhysicalCard

class Command(BaseCommand):
    help = 'Verify the card generation process with a custom template.'

    def handle(self, *args, **options):
        self.stdout.write("Starting card generation verification...")

        # 1. Get or create a test user
        User = get_user_model()
        user, created = User.objects.get_or_create(
            email='testuser@example.com',
            defaults={'first_name': 'Test', 'last_name': 'User'}
        )
        if created:
            user.set_password('password')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created test user: {user.email}'))
        else:
            self.stdout.write(f'Found existing test user: {user.email}')

        # 2. Create a PhysicalCardTemplate for testing
        template_image_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'safacard.png')
        if not os.path.exists(template_image_path):
            self.stderr.write(self.style.ERROR(f"Template image not found at {template_image_path}"))
            return

        template, created = PhysicalCardTemplate.objects.get_or_create(
            name='Test Template',
            defaults={
                'template_type': 'STANDARD',
                'card_width': 1012,
                'card_height': 638,
                'name_position_x': 100,
                'name_position_y': 200,
                'qr_position_x': 850,
                'qr_position_y': 50,
            }
        )
        if created:
            with open(template_image_path, 'rb') as f:
                template.card_front_image.save('test_template.png', ImageFile(f))
            template.save()
            self.stdout.write(self.style.SUCCESS(f'Created test template: {template.name}'))
        else:
            self.stdout.write(f'Found existing test template: {template.name}')

        # 3. Create a DigitalCard for the user and assign the template
        digital_card, created = DigitalCard.objects.get_or_create(
            user=user,
            defaults={
                'expires_date': date(2025, 12, 31),
            }
        )
        digital_card.template = template
        digital_card.save()
        self.stdout.write(f'Assigned template "{template.name}" to digital card for {user.email}')

        # 4. Generate the card image
        generator = SAFACardGenerator()
        try:
            card_image = generator.generate_card_image(user)
            output_path = os.path.join(settings.BASE_DIR, 'test_card_output.png')
            card_image.save(output_path, 'PNG')
            self.stdout.write(self.style.SUCCESS(f'Successfully generated card image and saved to {output_path}'))
            self.stdout.write("Please visually inspect the generated image to confirm the template and layout were used correctly.")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error generating card image: {e}'))

        # 5. Test CSV Export
        self.stdout.write("\nTesting CSV export...")
        factory = RequestFactory()
        request = factory.get('/export/csv/')
        request.user = user
        user.is_staff = True # Mock staff user
        try:
            response = export_cards_csv(request)
            if response.status_code == 200 and 'text/csv' in response['Content-Type']:
                csv_content = response.content.decode('utf-8')
                if 'Test User' in csv_content:
                    self.stdout.write(self.style.SUCCESS('CSV export test passed.'))
                    # Optionally save the CSV for inspection
                    with open('test_export.csv', 'w') as f:
                        f.write(csv_content)
                    self.stdout.write('CSV file saved to test_export.csv')
                else:
                    self.stderr.write(self.style.ERROR('CSV export failed: Test user not found in CSV content.'))
            else:
                self.stderr.write(self.style.ERROR(f'CSV export failed with status code {response.status_code}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'An error occurred during CSV export test: {e}'))


        # 6. Test PDF Export
        self.stdout.write("\nTesting PDF export...")
        physical_card, created = PhysicalCard.objects.get_or_create(
            user=user,
            defaults={'card_number': digital_card.card_number, 'template': template}
        )
        try:
            pdf_data = generate_print_ready_pdf([physical_card])
            if pdf_data:
                output_path = os.path.join(settings.BASE_DIR, 'test_card_output.pdf')
                with open(output_path, 'wb') as f:
                    f.write(pdf_data)
                self.stdout.write(self.style.SUCCESS(f'Successfully generated PDF and saved to {output_path}'))
            else:
                self.stderr.write(self.style.ERROR('PDF generation returned no data.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'An error occurred during PDF export test: {e}'))


        self.stdout.write("\nVerification script finished.")
