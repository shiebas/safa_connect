from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import Province, Region, GeographyUpdateLog, NationalFederation, Country

User = get_user_model()

class GeographyUpdateLogModelTest(TestCase):
    def setUp(self):
        self.national_admin = User.objects.create_user(
            email='national@test.com',
            password='password',
            role='ADMIN_NATIONAL',
            first_name='National',
            last_name='Admin'
        )
        self.province_admin = User.objects.create_user(
            email='province@test.com',
            password='password',
            role='ADMIN_PROVINCE',
            first_name='Province',
            last_name='Admin'
        )
        country = Country.objects.create(name='South Africa', code='RSA')
        self.national_federation = NationalFederation.objects.create(name='SAFA', country=country)
        self.province = Province.objects.create(name='Test Province', code='TP', national_federation=self.national_federation)
        self.province_admin.province = self.province
        self.province_admin.save()
        self.region = Region.objects.create(name='Test Region', code='TR', province=self.province)

    def test_approve_province_change(self):
        update_log = GeographyUpdateLog.objects.create(
            user=self.province_admin,
            content_object=self.province,
            field_name='name',
            old_value='Test Province',
            new_value='New Province Name'
        )
        update_log.approve(self.national_admin)
        self.province.refresh_from_db()
        self.assertEqual(self.province.name, 'New Province Name')
        self.assertEqual(update_log.status, 'APPROVED')
        self.assertEqual(update_log.approved_by, self.national_admin)

    def test_reject_province_change(self):
        update_log = GeographyUpdateLog.objects.create(
            user=self.province_admin,
            content_object=self.province,
            field_name='name',
            old_value='Test Province',
            new_value='New Province Name'
        )
        update_log.reject(self.national_admin)
        self.province.refresh_from_db()
        self.assertEqual(self.province.name, 'Test Province')
        self.assertEqual(update_log.status, 'REJECTED')
        self.assertEqual(update_log.approved_by, self.national_admin)


class GeographyManagementViewTest(TestCase):
    def setUp(self):
        self.national_admin = User.objects.create_user(
            email='national@test.com',
            password='password',
            role='ADMIN_NATIONAL',
            first_name='National',
            last_name='Admin'
        )
        self.province_admin = User.objects.create_user(
            email='province@test.com',
            password='password',
            role='ADMIN_PROVINCE',
            first_name='Province',
            last_name='Admin'
        )
        country = Country.objects.create(name='South Africa', code='RSA')
        self.national_federation = NationalFederation.objects.create(name='SAFA', country=country)
        self.province = Province.objects.create(name='Test Province', code='TP', national_federation=self.national_federation)
        self.province_admin.province = self.province
        self.province_admin.save()
        self.region = Region.objects.create(name='Test Region', code='TR', province=self.province)
        self.client.login(email='national@test.com', password='password')

    def test_view_as_national_admin(self):
        response = self.client.get('/geography/management/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['level'], 'Province')
        self.assertEqual(len(response.context['formset']), 1)

    def test_view_as_province_admin(self):
        self.client.login(email='province@test.com', password='password')
        response = self.client.get('/geography/management/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['level'], 'Region')
        self.assertEqual(len(response.context['formset']), 1)

    def test_submit_change_as_province_admin(self):
        self.client.login(email='province@test.com', password='password')
        response = self.client.post('/geography/management/', {
            'regions-TOTAL_FORMS': '1',
            'regions-INITIAL_FORMS': '1',
            'regions-MIN_NUM_FORMS': '0',
            'regions-MAX_NUM_FORMS': '1000',
            'regions-0-id': self.region.id,
            'regions-0-name': 'New Region Name',
            'regions-0-code': 'NR',
            'regions-0-description': 'New description',
            'regions-0-status': 'ACTIVE',
            'regions-0-is_compliant': 'on'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(GeographyUpdateLog.objects.filter(object_id=self.region.id).exists())

    def test_approve_change_as_national_admin(self):
        update_log = GeographyUpdateLog.objects.create(
            user=self.province_admin,
            content_object=self.province,
            field_name='name',
            old_value='Test Province',
            new_value='New Province Name'
        )
        response = self.client.post('/geography/management/', {'approve': update_log.id})
        self.assertEqual(response.status_code, 302)
        self.province.refresh_from_db()
        self.assertEqual(self.province.name, 'New Province Name')
        update_log.refresh_from_db()
        self.assertEqual(update_log.status, 'APPROVED')

    def test_province_admin_cannot_approve_province_change(self):
        self.client.login(email='province@test.com', password='password')
        update_log = GeographyUpdateLog.objects.create(
            user=self.national_admin,
            content_object=self.province,
            field_name='name',
            old_value='Test Province',
            new_value='New Province Name'
        )
        response = self.client.post('/geography/management/', {'approve': update_log.id})
        self.assertEqual(response.status_code, 302) # Redirects with error message
        self.province.refresh_from_db()
        self.assertEqual(self.province.name, 'Test Province') # Name should not have changed
        update_log.refresh_from_db()
        self.assertEqual(update_log.status, 'PENDING')
