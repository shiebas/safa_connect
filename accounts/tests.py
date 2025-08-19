from django.test import TestCase
from django.utils import timezone
from .models import CustomUser

class UserModelTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='password',
            first_name='Test',
            last_name='User',
            date_of_birth=timezone.datetime(2000, 1, 1).date()
        )

    def test_age_calculation(self):
        """
        Test that the age property on the CustomUser model is calculated correctly.
        """
        # This test is dependent on the current date, so we calculate the expected age dynamically.
        today = timezone.now().date()
        born = self.user.date_of_birth
        expected_age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        self.assertEqual(self.user.age, expected_age)

    def test_profile_picture_compliance(self):
        """
        Test that the compliance check correctly identifies if a profile picture is missing or present.
        """
        # Initially, the user should not have a profile picture.
        self.assertFalse(self.user.profile_picture)

        # After adding a profile picture, the check should pass.
        # Note: In a real test, you would mock a file upload. Here we simulate it.
        self.user.profile_picture = 'profile_pics/test.jpg'
        self.user.save()
        self.assertTrue(self.user.profile_picture)
