from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser, OrganizationType, Position
from membership.models import Member
from geography.models import Country, NationalFederation, Province, Region, LocalFootballAssociation, Club
from PIL import Image
import io
from django.core.files.uploadedfile import SimpleUploadedFile

def create_test_image():
    """Create a small, valid image for testing."""
    file = io.BytesIO()
    image = Image.new('RGB', (100, 100), 'white')
    image.save(file, 'jpeg')
    file.name = 'test.jpg'
    file.seek(0)
    return SimpleUploadedFile(file.name, file.read(), content_type='image/jpeg')

class UserRegistrationTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.country = Country.objects.create(name='South Africa')
        self.national_federation = NationalFederation.objects.create(name='SAFA', country=self.country)
        self.province = Province.objects.create(name='Test Province', national_federation=self.national_federation)
        self.region = Region.objects.create(name='Test Region', province=self.province)
        self.lfa = LocalFootballAssociation.objects.create(name='Test LFA', region=self.region)
        self.club = Club.objects.create(name='Test Club', localfootballassociation=self.lfa)

        self.form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'testuser@example.com',
            'password': 'ComplexPassword123!',
            'password2': 'ComplexPassword123!',
            'role': 'PLAYER',
            'popi_act_consent': True,
            'id_document_type': 'ID',
            'id_number': '8001015009087', # Valid ID
            'date_of_birth': '1980-01-01',
            'gender': 'M',
            'country_code': '+27',
            'nationality': 'South African',
            'country': self.country.id,
            'province': self.province.id,
        }

    def test_user_registration_page_loads(self):
        response = self.client.get(reverse('accounts:user_registration'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/user_registration.html')

    def test_valid_form_submission(self):
        response = self.client.post(reverse('accounts:user_registration'), self.form_data)
        self.assertEqual(response.status_code, 302) # Should redirect on success
        self.assertTrue(CustomUser.objects.filter(email='testuser@example.com').exists())
        self.assertTrue(Member.objects.filter(email='testuser@example.com').exists())
        member = Member.objects.get(email='testuser@example.com')
        self.assertEqual(member.role, 'PLAYER')

    def test_password_mismatch(self):
        data = self.form_data.copy()
        data['password2'] = 'WrongPassword'
        response = self.client.post(reverse('accounts:user_registration'), data)
        self.assertEqual(response.status_code, 200) # Should re-render the form
        self.assertFalse(CustomUser.objects.filter(email='testuser@example.com').exists())

    def test_role_selection(self):
        data = self.form_data.copy()
        data['role'] = 'OFFICIAL'
        response = self.client.post(reverse('accounts:user_registration'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Member.objects.filter(email='testuser@example.com').exists())
        member = Member.objects.get(email='testuser@example.com')
        self.assertEqual(member.role, 'OFFICIAL')

    def test_add_club_administrator(self):
        # Create a club admin to perform the action
        club_admin_user = CustomUser.objects.create_user(
            email='clubadmin@example.com',
            password='ComplexPassword123!',
            role='CLUB_ADMIN',
            club=self.club,
            is_staff=True
        )
        self.client.login(email='clubadmin@example.com', password='ComplexPassword123!')

        admin_form_data = {
            'first_name': 'New',
            'last_name': 'Admin',
            'email': 'newadmin@example.com',
            'password': 'NewAdminPassword123!',
            'password2': 'NewAdminPassword123!',
            'phone_number': '1234567890',
            'id_document_type': 'ID',
            'id_number': '8101015009088', # Valid ID for a different person
            'popi_act_consent': True,
        }

        response = self.client.post(reverse('accounts:add_club_administrator'), admin_form_data)
        self.assertEqual(response.status_code, 302) # Should redirect on success

        # Check if the new admin was created
        self.assertTrue(CustomUser.objects.filter(email='newadmin@example.com').exists())
        new_admin = CustomUser.objects.get(email='newadmin@example.com')
        self.assertEqual(new_admin.role, 'CLUB_ADMIN')
        self.assertTrue(new_admin.is_staff)
        self.assertEqual(new_admin.club, self.club)

        # Check that the password is hashed correctly
        self.assertTrue(new_admin.check_password('NewAdminPassword123!'))
        self.assertNotEqual(new_admin.password, 'NewAdminPassword123!')
