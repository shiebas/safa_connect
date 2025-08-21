from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.forms import NationalAdminRegistrationForm
from accounts.models import OrganizationType, Position
from geography.models import Province, Region, LocalFootballAssociation, Club
from PIL import Image
import io

def create_test_image():
    """Create a small, valid image for testing."""
    file = io.BytesIO()
    image = Image.new('RGB', (100, 100), 'white')
    image.save(file, 'jpeg')
    file.name = 'test.jpg'
    file.seek(0)
    return SimpleUploadedFile(file.name, file.read(), content_type='image/jpeg')

class NationalAdminRegistrationFormTests(TestCase):

    def setUp(self):
        # Create necessary geographic objects
        self.province = Province.objects.create(name='Test Province')
        self.region = Region.objects.create(name='Test Region', province=self.province)
        self.lfa = LocalFootballAssociation.objects.create(name='Test LFA', region=self.region)
        self.club = Club.objects.create(name='Test Club', localfootballassociation=self.lfa)

        # Create other necessary objects for the form
        self.org_type_club = OrganizationType.objects.create(name='Club', level='CLUB')
        self.position = Position.objects.create(title='Test Position', employment_type='MEMBER')

        self.form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'testuser@example.com',
            'password': 'ComplexPassword123!',
            'password2': 'ComplexPassword123!',
            'organization_type': self.org_type_club.id,
            'position': self.position.id,
            'popi_act_consent': True,
            'province': self.province.id,
            'region': self.region.id,
            'local_federation': self.lfa.id,
            'club': self.club.id,
        }

    def test_valid_form(self):
        # Test with minimum valid data
        data = self.form_data.copy()
        data.update({
            'id_document_type': 'PP',
            'passport_number': 'A12345678',
            'date_of_birth': '1990-01-01',
            'gender': 'M',
        })
        form = NationalAdminRegistrationForm(data)
        form.fields['region'].queryset = Region.objects.all()
        form.fields['local_federation'].queryset = LocalFootballAssociation.objects.all()
        form.fields['club'].queryset = Club.objects.all()
        self.assertTrue(form.is_valid(), form.errors)

    def test_password_mismatch(self):
        data = self.form_data.copy()
        data.pop('province')
        data.pop('region')
        data.pop('local_federation')
        data.pop('club')
        data['password2'] = 'WrongPassword'
        form = NationalAdminRegistrationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_conditional_geo_fields_required(self):
        data = self.form_data.copy()
        data.update({
            'id_document_type': 'PP',
            'passport_number': 'A12345678',
            'date_of_birth': '1990-01-01',
            'gender': 'M',
        })
        data.pop('club')
        # Test that club is required for 'Club' org type
        form = NationalAdminRegistrationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('club', form.errors)

    def test_sa_id_validation(self):
        data = self.form_data.copy()
        data.update({
            'id_document_type': 'ID',
            'id_number': '9001015800087', # Valid ID
        })
        form = NationalAdminRegistrationForm(data)
        form.fields['region'].queryset = Region.objects.all()
        form.fields['local_federation'].queryset = LocalFootballAssociation.objects.all()
        form.fields['club'].queryset = Club.objects.all()
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(str(form.cleaned_data['date_of_birth']), '1990-01-01')
        self.assertEqual(form.cleaned_data['gender'], 'M')

    def test_invalid_sa_id(self):
        data = self.form_data.copy()
        data.update({
            'id_document_type': 'ID',
            'id_number': '1234567890123', # Invalid ID
        })
        form = NationalAdminRegistrationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('id_number', form.errors)

    def test_file_upload_validation(self):
        # Test valid file
        image = create_test_image()
        data = self.form_data.copy()
        data.update({
            'id_document_type': 'PP',
            'passport_number': 'A12345678',
            'date_of_birth': '1990-01-01',
            'gender': 'M',
        })
        files = {'profile_picture': image}
        form = NationalAdminRegistrationForm(data, files)
        form.fields['region'].queryset = Region.objects.all()
        form.fields['local_federation'].queryset = LocalFootballAssociation.objects.all()
        form.fields['club'].queryset = Club.objects.all()
        self.assertTrue(form.is_valid(), form.errors)

        # Test oversized file
        large_file = SimpleUploadedFile("large.jpg", b"a" * (6 * 1024 * 1024), content_type="image/jpeg")
        files = {'profile_picture': large_file}
        form = NationalAdminRegistrationForm(data, files)
        self.assertFalse(form.is_valid())
        self.assertIn('profile_picture', form.errors)

        # Test invalid file type
        invalid_file = SimpleUploadedFile("test.txt", b"file_content", content_type="text/plain")
        files = {'profile_picture': invalid_file}
        form = NationalAdminRegistrationForm(data, files)
        self.assertFalse(form.is_valid())
        self.assertIn('profile_picture', form.errors)
