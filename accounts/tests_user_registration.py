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
            'id_document_type': 'PP',
            'passport_number': 'A12345678',
            'date_of_birth': '1990-01-01',
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
