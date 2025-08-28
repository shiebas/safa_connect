from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser, OrganizationType, Position
from membership.models import Member, SAFASeasonConfig, RegistrationWorkflow, Invoice, SAFAFeeStructure
from geography.models import Country, NationalFederation, Province, Region, LocalFootballAssociation, Club
from PIL import Image
import io
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal

def create_test_image():
    """Create a small, valid image for testing."""
    file = io.BytesIO()
    image = Image.new('RGB', (100, 100), 'white')
    image.save(file, 'jpeg')
    file.name = 'test.jpg'
    file.seek(0)
    return SimpleUploadedFile(file.name, file.read(), content_type='image/jpeg')

from accounts.models import Association


class UserRegistrationTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.country = Country.objects.create(name='South Africa')
        self.national_federation = NationalFederation.objects.create(name='SAFA', country=self.country)
        self.province = Province.objects.create(name='Test Province', national_federation=self.national_federation)
        self.region = Region.objects.create(name='Test Region', province=self.province)
        self.lfa = LocalFootballAssociation.objects.create(name='Test LFA', region=self.region)
        self.club = Club.objects.create(name='Test Club', localfootballassociation=self.lfa)
        self.association = Association.objects.create(name='Test Association', national_federation=self.national_federation)
        self.admin_user = CustomUser.objects.create_user(email='admin@test.com', password='password')
        self.season = SAFASeasonConfig.objects.create(
            season_year=2025,
            is_active=True,
            season_start_date='2025-01-01',
            season_end_date='2025-12-31',
            organization_registration_start='2025-01-01',
            organization_registration_end='2025-12-31',
            member_registration_start='2025-01-01',
            member_registration_end='2025-12-31',
            created_by=self.admin_user
        )

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

    def setUp(self):
        self.client = Client()
        self.country = Country.objects.create(name='South Africa')
        self.national_federation = NationalFederation.objects.create(name='SAFA', country=self.country)
        self.province = Province.objects.create(name='Test Province', national_federation=self.national_federation)
        self.region = Region.objects.create(name='Test Region', province=self.province)
        self.lfa = LocalFootballAssociation.objects.create(name='Test LFA', region=self.region)
        self.club = Club.objects.create(name='Test Club', localfootballassociation=self.lfa)
        self.association = Association.objects.create(name='Test Association', national_federation=self.national_federation)
        self.admin_user = CustomUser.objects.create_user(email='admin@test.com', password='password')
        self.season = SAFASeasonConfig.objects.create(
            season_year=2025,
            is_active=True,
            season_start_date='2025-01-01',
            season_end_date='2025-12-31',
            organization_registration_start='2025-01-01',
            organization_registration_end='2025-12-31',
            member_registration_start='2025-01-01',
            member_registration_end='2025-12-31',
            created_by=self.admin_user
        )
        # Create fee structures for invoicing
        SAFAFeeStructure.objects.create(
            season_config=self.season,
            entity_type='PLAYER_SENIOR',
            annual_fee=Decimal('125.00'),
            is_pro_rata=False,
            created_by=self.admin_user
        )
        SAFAFeeStructure.objects.create(
            season_config=self.season,
            entity_type='OFFICIAL_GENERAL',
            annual_fee=Decimal('50.00'),
            is_pro_rata=False,
            created_by=self.admin_user
        )

        self.form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'testuser@example.com',
            'password': 'ComplexPassword123!',
            'password2': 'ComplexPassword123!',
            'role': 'PLAYER',
            'popi_act_consent': True,
            'id_document_type': 'ID',
            'id_number': '8001015009087', # A valid ID number for the SA-specific Luhn
            'date_of_birth': '1980-01-01',
            'gender': 'M',
            'street_address': '123 Test Street',
            'city': 'Testville',
            'postal_code': '1234',
            'country_code': '+27',
            'nationality': 'South African',
            'country': self.country.id,
            'province': self.province.id,
        }

    def test_valid_new_member_registration(self):
        """
        Test a full, valid registration for a completely new member.
        This should create a User, Member, Workflow, and Invoice.
        """
        self.assertEqual(CustomUser.objects.count(), 1) # Just the admin user
        self.assertEqual(Member.objects.count(), 0)

        data = self.form_data.copy()
        data.update({
            'region': self.region.id,
            'lfa': self.lfa.id,
            'club': self.club.id,
            'profile_picture': create_test_image(),
        })

        response = self.client.post(reverse('accounts:user_registration'), data, follow=True)

        # Check that the user, member, and workflow were created
        self.assertEqual(CustomUser.objects.count(), 2)
        self.assertEqual(Member.objects.count(), 1)
        self.assertTrue(RegistrationWorkflow.objects.filter(member__email='testuser@example.com').exists())

        user = CustomUser.objects.get(email='testuser@example.com')
        member = Member.objects.get(email='testuser@example.com')
        workflow = RegistrationWorkflow.objects.get(member=member)

        # Verify User data
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.role, 'PLAYER')
        self.assertEqual(user.street_address, '123 Test Street')
        self.assertEqual(user.club, self.club)

        # Verify Member data (and data sync)
        self.assertEqual(member.user, user)
        self.assertEqual(member.role, 'PLAYER')
        self.assertEqual(member.street_address, user.street_address)
        self.assertEqual(member.current_club, self.club)
        self.assertNotEqual(member.safa_id, None)

        # Verify Workflow status
        self.assertEqual(workflow.current_step, 'PAYMENT')

        # Verify Invoice creation
        self.assertTrue(Invoice.objects.filter(member=member).exists())
        invoice = Invoice.objects.get(member=member)
        self.assertEqual(invoice.status, 'PENDING')
        # annual_fee=125.00, vat_rate=0.15 -> total = 125.00 * 1.15 = 143.75
        self.assertEqual(invoice.total_amount, Decimal('143.75'))

        # Check for successful redirect to invoice page
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('membership:invoice_detail', kwargs={'uuid': invoice.uuid}))

    def test_password_mismatch(self):
        data = self.form_data.copy()
        data['password2'] = 'WrongPassword'
        response = self.client.post(reverse('accounts:user_registration'), data)
        self.assertEqual(response.status_code, 200) # Should re-render the form
        self.assertFalse(CustomUser.objects.filter(email='testuser@example.com').exists())

    def test_official_registration(self):
        """
        Test that an official is created correctly and the correct fee is applied.
        """
        data = self.form_data.copy()
        data.update({
            'role': 'OFFICIAL',
            'association': self.association.id,
        })
        # Officials might not belong to a club, so we remove the key
        data.pop('club', None)
        response = self.client.post(reverse('accounts:user_registration'), data, follow=True)

        self.assertTrue(Member.objects.filter(email='testuser@example.com').exists())
        member = Member.objects.get(email='testuser@example.com')
        self.assertEqual(member.role, 'OFFICIAL')
        self.assertTrue(member.associations.filter(id=self.association.id).exists())

        # Verify Invoice creation with the correct fee for an official
        self.assertTrue(Invoice.objects.filter(member=member).exists())
        invoice = Invoice.objects.get(member=member)
        # annual_fee=50.00, vat_rate=0.15 -> total = 50.00 * 1.15 = 57.50
        self.assertEqual(invoice.total_amount, Decimal('57.50'))
        self.assertRedirects(response, reverse('membership:invoice_detail', kwargs={'uuid': invoice.uuid}))

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
            'id_number': '9001015800087',
            'popi_act_consent': True,
            'street_address': '456 Admin Ave',
            'city': 'Admintown',
            'postal_code': '5678',
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


    def test_registration_of_existing_unlinked_member(self):
        """
        Test registering by claiming an existing, unlinked Member profile.
        This should create a new User, link it to the existing Member,
        update the Member's data, and proceed to invoicing.
        """
        # 1. Create an existing member without a user account
        existing_member = Member.objects.create(
            safa_id='EXT12',
            first_name='Existing',
            last_name='Person',
            email='old-email@example.com',
            role='PLAYER',
            street_address='Old Address',
            current_club=self.club,
        )
        self.assertEqual(Member.objects.count(), 1)
        self.assertEqual(CustomUser.objects.count(), 1)

        # 2. Prepare form data to claim this member
        data = self.form_data.copy()
        data.update({
            'is_existing_member': True,
            'previous_safa_id': 'EXT12',
            'email': 'new-email@example.com', # User is updating their email
            'first_name': 'Updated', # User is updating their name
            'street_address': '99 New Street',
            'province': self.province.id,
            'region': self.region.id,
            'lfa': self.lfa.id,
            'club': self.club.id,
        })

        response = self.client.post(reverse('accounts:user_registration'), data, follow=True)

        # 3. Verify the outcome
        self.assertEqual(Member.objects.count(), 1) # No new member created
        self.assertEqual(CustomUser.objects.count(), 2) # A new user was created

        # Get the updated member and new user
        member = Member.objects.get(safa_id='EXT12')
        user = CustomUser.objects.get(email='new-email@example.com')

        # Check that the user is linked to the member
        self.assertEqual(member.user, user)

        # Check that the member's details were updated from the form
        self.assertEqual(member.first_name, 'Updated')
        self.assertEqual(member.email, 'new-email@example.com')
        self.assertEqual(member.street_address, '99 New Street')

        # Check that the user's details are consistent
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.street_address, '99 New Street')

        # Check that the workflow and invoice were created
        self.assertTrue(RegistrationWorkflow.objects.filter(member=member).exists())
        self.assertTrue(Invoice.objects.filter(member=member).exists())

    def test_registration_of_existing_linked_member_fails(self):
        """
        Test that registering by claiming a Member profile that is already
        linked to a User account fails gracefully.
        """
        # 1. Create an existing user and member, and link them
        linked_user = CustomUser.objects.create_user(email='linked@test.com', password='password')
        linked_member = Member.objects.create(
            user=linked_user,
            safa_id='LNK45',
            first_name='Linked',
            last_name='Person',
            email='linked@test.com',
            current_club=self.club,
        )
        self.assertEqual(Member.objects.count(), 1)
        self.assertEqual(CustomUser.objects.count(), 2)

        # 2. Attempt to claim this member with a new user registration
        data = self.form_data.copy()
        data.update({
            'is_existing_member': True,
            'previous_safa_id': 'LNK45',
            'province': self.province.id,
            'region': self.region.id,
            'lfa': self.lfa.id,
            'club': self.club.id,
        })

        response = self.client.post(reverse('accounts:user_registration'), data)

        # 3. Verify the failure
        self.assertEqual(response.status_code, 200) # Should re-render the form
        self.assertContains(response, "This member account is already linked to a user account.")
        self.assertEqual(Member.objects.count(), 1) # No new member created
        self.assertEqual(CustomUser.objects.count(), 2) # No new user created

    def test_registration_with_invalid_safa_id_fails(self):
        """
        Test that registering with a non-existent SAFA ID fails gracefully.
        """
        data = self.form_data.copy()
        data.update({
            'is_existing_member': True,
            'previous_safa_id': 'BOGUS',
            'province': self.province.id,
            'region': self.region.id,
            'lfa': self.lfa.id,
            'club': self.club.id,
        })

        response = self.client.post(reverse('accounts:user_registration'), data)

        self.assertEqual(response.status_code, 200) # Re-renders form
        self.assertContains(response, "No member found with the provided SAFA ID.")
        self.assertEqual(CustomUser.objects.count(), 1) # No new user
        self.assertEqual(Member.objects.count(), 0) # No new member
