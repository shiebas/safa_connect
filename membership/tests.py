from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser
from django.core.files.uploadedfile import SimpleUploadedFile
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

class MembershipPDFExportTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='testuser@example.com',
            password='ComplexPassword123!',
            first_name='Test',
            last_name='User',
            safa_id='12345'
        )
        self.client.login(email='testuser@example.com', password='ComplexPassword123!')

    def test_export_profile_pdf_view(self):
        """Test that the export_profile_pdf view returns a PDF response."""
        response = self.client.get(reverse('membership:export_profile_pdf', args=[self.user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response['Content-Disposition'].startswith('attachment; filename='))
        self.assertTrue(response['Content-Disposition'].endswith('_profile.pdf"'))
        # Check that the PDF content is not empty
        self.assertTrue(len(response.content) > 100) # Check for some minimal content
