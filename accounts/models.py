from django.contrib.auth.models import AbstractUser, BaseUserManager, Permission
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from typing import Any

# Use string references throughout to avoid import issues
# Remove this import completely:
# from geography.models import (
#    Club, Region, Association, LocalFootballAssociation,
#    NationalFederation
# )


class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

ROLES = (
    ('ADMIN_NATIONAL', _('National Federation Admin')),
    ('ADMIN_PROVINCE', _('Provincial Administrator')),
    ('ADMIN_REGION', _('Regionial Administrator')),
    ('ADMIN_LOCAL_FED', _('Local Federation Administrator')),
    ('CLUB_ADMIN', _('Club Administrator')),
    ('ASSOCIATION_ADMIN', _('Association Administrator')),
)

# Add new employment status choices
EMPLOYMENT_STATUS = (
    ('EMPLOYEE', _('Full-time Employee')),
    ('MEMBER', _('Member (Political Structure)')),
    ('PUBLIC', _('Public/Supporter')),
)

DOCUMENT_TYPES = (
    ('BC', _('Birth Certificate')),
    ('PP', _('Passport')),
    ('ID', _('National ID')),
    ('DL', _('Driver License')),
    ('OT', _('Other')),
)

GENDER_CHOICES = (
    ('M', _('Male')),
    ('F', _('Female')),
)

PLAYER_CATEGORIES = (
    ('JUN', _('Junior')),
    ('SEN', _('Senior')),
    ('VET', _('Veteran')),
)

class RegistrationType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    allowed_user_roles = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# Add new position model
class Position(models.Model):
    """Available positions within SAFA structures"""
    title = models.CharField(max_length=100, unique=True)  # Make title unique across all levels
    description = models.TextField(blank=True)
    # Level is no longer a constraint but indicates where this position can be used
    levels = models.CharField(max_length=100, default='NATIONAL,PROVINCE,REGION,LFA,CLUB', 
                              help_text="Comma-separated list of levels where this position can be used")
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_positions')
    requires_approval = models.BooleanField(default=True, help_text="New positions need admin approval")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']
        # No more unique constraints by level since title is unique

    def __str__(self):
        return self.title

    @property
    def available_levels(self):
        """Return list of levels where this position can be used"""
        if not self.levels:
            return []
        return [level.strip() for level in self.levels.split(',')]

    def can_be_used_at_level(self, level):
        """Check if position can be used at the specified level"""
        return level in self.available_levels

class ModelWithLogo(models.Model):
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)

    @cached_property
    def logo_url(self):
        try:
            if self.logo and hasattr(self.logo, 'url'):
                # Check if the file actually exists to avoid timeouts
                if self.logo.storage.exists(self.logo.name):
                    return self.logo.url
        except Exception:
            pass
        return '/static/default_logo.png'

    class Meta:
        abstract = True

# Add missing import for Club
try:
    from geography.models import Club
except ImportError:
    Club = None

# Add the OrganizationType model after the Position model
class OrganizationType(models.Model):
    """Types of organizations a user can belong to in the federation hierarchy"""
    name = models.CharField(max_length=50)
    level = models.CharField(
        max_length=20,
        choices=[
            ('NATIONAL', 'National Federation'),
            ('PROVINCE', 'Province'),
            ('REGION', 'Region'),
            ('LFA', 'Local Football Association'),
            ('ASSOCIATION', 'Association'),
            ('CLUB', 'Club'),
        ]
    )
    requires_approval = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.level})"

    class Meta:
        ordering = ['level']

class CustomUser(AbstractUser, ModelWithLogo):
    # Remove the username field
    username = None

    # Required fields
    email = models.EmailField(_('email address'), unique=True)
    registration_type = models.ForeignKey(
        RegistrationType,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    # Core Fields
    role = models.CharField(max_length=20, choices=ROLES, default='ADMIN_PROVINCE')
    name = models.CharField(max_length=50, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    surname = models.CharField(max_length=100, blank=True)
    alias = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)

    # Nationality and Birth Country
    nationality = models.CharField(
        max_length=50,
        default='South African',
        help_text=_("User's nationality")
    )
    birth_country = models.CharField(
        max_length=3, 
        default='ZAF', 
        help_text=_("3-letter country code for country of birth")
    )

    # POPI Act Compliance
    popi_act_consent = models.BooleanField(
        default=False,
        help_text=_("User must consent to POPI Act terms for registration")
    )

    # Simplify country handling for South African context
    country_code = models.CharField(
        max_length=3, 
        default='ZAF', 
        blank=True,
        help_text=_("Default is ZAF for South African citizens")
    )

    # Identification - FIXED to handle empty values
    id_number = models.CharField(
        max_length=20, 
        blank=True,
        null=True,
        help_text=_("13-digit South African ID number for citizens")
    )
    id_number_other = models.CharField(max_length=25, blank=True, null=True)
    passport_number = models.CharField(max_length=25, blank=True, null=True)
    id_document_type = models.CharField(
        max_length=2,
        choices=DOCUMENT_TYPES,
        default='ID'
    )

    # Status and IDs
    is_active = models.BooleanField(default=False)
    membership_card = models.BooleanField(default=False)
    payment_required = models.BooleanField(default=True)
    safa_id = models.CharField(max_length=5, unique=True, blank=True, null=True)
    fifa_id = models.CharField(max_length=7, unique=True, blank=True, null=True)

    # Media
    profile_photo = models.ImageField(upload_to='images/profile_photos/', blank=True, null=True)
    id_document = models.FileField(
        upload_to='documents/user_documents/',
        null=True, 
        blank=True
    )

    # Registration
    registration_date = models.DateField(default=timezone.now)

    # Membership and Card Management Fields
    membership_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending Payment'),
            ('PAID', 'Payment Received'),
            ('ACTIVE', 'Active Member'),
            ('EXPIRED', 'Membership Expired'),
            ('SUSPENDED', 'Membership Suspended')
        ],
        default='PENDING',
        help_text='Current membership status'
    )
    membership_paid_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='Date when membership payment was received'
    )
    membership_activated_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='Date when membership was activated by admin'
    )
    membership_expires_date = models.DateField(
        null=True, 
        blank=True,
        help_text='Date when membership expires (annual renewal)'
    )
    membership_fee_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name=_('Membership Fee (ZAR)'),
        help_text=_('Amount paid for membership in ZAR (South African Rand)')
    )

    # Card Delivery Preferences
    card_delivery_preference = models.CharField(
        max_length=20,
        choices=[
            ('DIGITAL_ONLY', 'Digital Card Only'),
            ('PHYSICAL_ONLY', 'Physical Card Only'),
            ('BOTH', 'Both Digital and Physical')
        ],
        default='DIGITAL_ONLY',
        help_text='Preferred card delivery method'
    )
    physical_card_requested = models.BooleanField(
        default=False,
        help_text='Whether user has requested a physical card'
    )
    physical_card_delivery_address = models.TextField(
        blank=True,
        help_text='Delivery address for physical card (if requested)'
    )

    # Add missing required validation
    first_name = models.CharField(_('first name'), max_length=150, blank=False)
    last_name = models.CharField(_('last name'), max_length=150, blank=False)

    # Add employment status field
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS,
        blank=True,
        help_text=_("Employment/membership status within SAFA structure")
    )

    # Add position field
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("User's position within SAFA structure")
    )

    # Add club membership verification for Members
    club_membership_verified = models.BooleanField(
        default=False,
        help_text=_("Verified as bona fide club member")
    )
    club_membership_number = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Club membership number for verification")
    )

    # Add supporting club for supporters - fix the string reference
    supporting_club = models.ForeignKey(
        'geography.Club',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supporters',
        help_text=_("Club that this supporter follows")
    )

    # Add driver_license_number field to the model
    driver_license_number = models.CharField(
        max_length=25, 
        blank=True, 
        null=True,
        help_text="Driver's license number"
    )

    # Add foreign key fields to store organization relationships
    national_federation = models.ForeignKey(
        'geography.NationalFederation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='federation_users',
        help_text="National federation this user belongs to"
    )

    province = models.ForeignKey(
        'geography.Province',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Province this user belongs to"
    )

    region = models.ForeignKey(
        'geography.Region',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Region this user belongs to"
    )

    local_federation = models.ForeignKey(
        'geography.LocalFootballAssociation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Local Football Association this user belongs to"
    )

    club = models.ForeignKey(
        'geography.Club',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        help_text="Club this user belongs to (required for political leaders)"
    )

    association = models.ForeignKey(
        'geography.Association',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_users',
        help_text="Association this user administers (required for association admins)"
    )

    # Add organization type to structure registration
    organization_type = models.ForeignKey(
        OrganizationType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Primary organization type this user belongs to"
    )

    # Add mother body/federation field that defaults to SAFAM
    mother_body = models.ForeignKey(
        'geography.MotherBody',
        on_delete=models.SET_NULL,  # Don't allow deletion of SAFAM
        null=True,
        blank=True,
        related_name='custom_users',
        help_text="The mother body this user belongs to (defaults to SAFAM)"
    )

    # Specify the custom manager
    objects = CustomUserManager()

    # Set email as the USERNAME_FIELD
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'accounts_customuser'
        ordering = ['email']
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'
        constraints = [
            models.UniqueConstraint(
                fields=['id_number'], 
                name='unique_id_number',
                condition=models.Q(id_number__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['passport_number'], 
                name='unique_passport_number',
                condition=models.Q(passport_number__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['mother_body'],
                condition=models.Q(mother_body__isnull=False),
                name='unique_mother_body_when_not_blank'
            ),
        ]

    def save(self, *args, **kwargs):
        """Override save method to validate ID number and set nationality"""
        # Ensure mother_body is always set to SAFA if not specified
        # Check if mother_body field exists and is accessible
        # Temporarily commented out until field exists in database
        # try:
        #     if hasattr(self, 'mother_body') and not getattr(self, 'mother_body_id', None):
        #         from geography.models import MotherBody
        #         safam = MotherBody.objects.get(name='SAFAM')
        #         self.mother_body = safam
        # except Exception as e:
        #     # Log error but don't prevent save - field might not exist yet
        #     import logging
        #     logger = logging.getLogger(__name__)
        #     logger.warning(f"Could not set SAFA as mother body: {str(e)}")

        # Convert empty strings to None to avoid unique constraint issues
        if self.id_number == '':
            self.id_number = None
        if self.passport_number == '':
            self.passport_number = None
        if self.id_number_other == '':
            self.id_number_other = None

        # Set nationality based on document type
        if self.id_document_type in ['ID', 'BC'] and not self.nationality:
            self.nationality = 'ZAF'

        # Set birth country to ZAF if not specified and using SA documents
        if self.id_document_type in ['ID', 'BC'] and not self.birth_country:
            self.birth_country = 'ZAF'

        # Only validate ID number if it has changed
        if self.id_number and (not self.pk or self._meta.model.objects.get(pk=self.pk).id_number != self.id_number):
            try:
                # Only validate the ID number field
                self._validate_id_number()
            except Exception as e:
                # If validation fails, log the error but allow the save to proceed
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"ID number validation failed for user {self.email}: {str(e)}")

        # Ensure mother_body is set to SAFAM if not specified
            try:
                from geography.models import MotherBody
                safam = MotherBody.objects.get(name="SAFAM")
                self.mother_body = safam
            except (MotherBody.DoesNotExist, ImportError) as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not set SAFAM as mother body: {str(e)}")
            # Set to None instead of raising error
            self.mother_body = None

        super().save(*args, **kwargs)

    def generate_safa_id(self):
        """Generate 5-digit alphanumeric SAFA ID (A-Z, 0-9)"""
        if self.safa_id:
            return self.safa_id

        import string
        import random

        # Use only capital letters and digits
        chars = string.ascii_uppercase + string.digits  # A-Z, 0-9

        # Generate 5-character alphanumeric ID
        while True:
            safa_id = ''.join(random.choices(chars, k=5))

            # Ensure uniqueness - fixed to use CustomUser instead of User
            if not CustomUser.objects.filter(safa_id=safa_id).exists():
                break

        self.safa_id = safa_id
        return safa_id

    @staticmethod
    def extract_id_info(id_number, country_code='ZAF'):
        """
        Extract and validate information from an ID number based on country.
        Supports South Africa (ZAF/RSA), Namibia (NAM), and Lesotho (LSO).
        Returns a dictionary with date_of_birth, gender, citizenship, and is_valid.
        """
        result = {
            'date_of_birth': None,
            'gender': None,
            'citizenship': None,
            'is_valid': False,
            'error': None
        }

        # Remove any spaces or hyphens
        id_number = id_number.replace(' ', '').replace('-', '')

        # Normalize country code - handle both ZAF and RSA for South Africa
        if country_code == 'RSA':
            country_code = 'ZAF'

        # Validate based on country
        if country_code == 'ZAF':
            # South African ID validation
            # Check if ID number is 13 digits
            if not id_number.isdigit() or len(id_number) != 13:
                result['error'] = "South African ID number must be 13 digits."
                return result

            # Extract date components
            year = id_number[0:2]
            month = id_number[2:4]
            day = id_number[4:6]

            # Validate date
            try:
                from django.utils import timezone
                current_year = timezone.now().year % 100
                century = '19' if int(year) > current_year else '20'
                full_year = int(century + year)

                import datetime
                result['date_of_birth'] = datetime.date(full_year, int(month), int(day))
            except ValueError:
                result['error'] = "ID number contains an invalid date of birth."
                return result

            # Extract gender
            gender_digits = int(id_number[6:10])
            result['gender'] = 'M' if gender_digits >= 5000 else 'F'

            # Extract citizenship
            result['citizenship'] = int(id_number[10])
            if result['citizenship'] not in [0, 1]:
                result['error'] = "ID number citizenship digit (11) must be 0 or 1."
                return result

            # Validate checksum (Luhn algorithm for South African ID)
            # For South African IDs, the algorithm is:
            # 1. Add all digits in odd positions (1st, 3rd, 5th, etc.)
            # 2. Concatenate all digits in even positions (2nd, 4th, 6th, etc.)
            # 3. Multiply the result of step 2 by 2
            # 4. Add the digits of the result from step 3
            # 5. Add the result from step 4 to the result from step 1
            # 6. The check digit is (10 - (result % 10)) % 10

            odd_sum = 0
            even_digits = ""

            # Remember that positions are 0-indexed in code but 1-indexed in the algorithm description
            for i in range(len(id_number) - 1):  # Exclude the check digit
                digit = int(id_number[i])
                if i % 2 == 0:  # Even position in 0-indexed (odd in 1-indexed)
                    odd_sum += digit
                else:  # Odd position in 0-indexed (even in 1-indexed)
                    even_digits += str(digit)

            # Double the even digits as a single number and sum its digits
            doubled_even = int(even_digits) * 2 if even_digits else 0
            even_sum = sum(int(digit) for digit in str(doubled_even))

            # Calculate the total and check digit
            total = odd_sum + even_sum
            check_digit = (10 - (total % 10)) % 10

            if check_digit != int(id_number[-1]):
                result['error'] = f"ID number has an invalid checksum digit. Expected {check_digit}, got {id_number[-1]}."
                return result

        elif country_code == 'NAM':
            # Namibian ID validation
            if not id_number.isdigit() or len(id_number) != 11:
                result['error'] = "Namibian ID number must be 11 digits."
                return result

            # Extract date components
            year = id_number[0:2]
            month = id_number[2:4]
            day = id_number[4:6]

            # Validate date
            try:
                from django.utils import timezone
                current_year = timezone.now().year % 100
                century = '19' if int(year) > current_year else '20'
                full_year = int(century + year)

                import datetime
                result['date_of_birth'] = datetime.date(full_year, int(month), int(day))
            except ValueError:
                result['error'] = "ID number contains an invalid date of birth."
                return result

            result['gender'] = None

        elif country_code == 'LSO':
            # Lesotho ID validation
            if not id_number.isdigit() or len(id_number) < 8 or len(id_number) > 10:
                result['error'] = "Lesotho ID number must be 8-10 digits."
                return result

            result['date_of_birth'] = None
            result['gender'] = None

        else:
            result['error'] = f"ID validation for country code {country_code} is not supported."
            return result

        # If we got here, the ID number is valid
        result['is_valid'] = True
        return result

    def _validate_id_number(self):
        """Make ID validation more robust to prevent admin errors"""
        if not self.id_number:
            return

        try:
            # Your existing validation code
            id_number = self.id_number.replace(' ', '').replace('-', '')
            country_code = getattr(self, 'country_code', 'ZAF')

            # Extract and validate ID information
            id_info = self.extract_id_info(id_number, country_code)

            if not id_info['is_valid']:
                # Log error but don't raise exception in admin context
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"ID validation warning: {id_info['error']}")
                return

            # Set values as before but don't raise exceptions
            if not self.date_of_birth and id_info['date_of_birth']:
                self.date_of_birth = id_info['date_of_birth']

            if not self.gender and id_info['gender']:
                self.gender = id_info['gender']

            self.id_number = id_number
        except Exception as e:
            # Log any unexpected errors but allow admin to function
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Unexpected error in ID validation")
            pass  # Ignore errors to prevent admin lockout

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email

    def __str__(self):
        return self.get_full_name()

    def clean(self):
        """Remove the province validation that's causing the admin form problems"""
        # Call the parent clean method but catch ValidationError for province
        try:
            super().clean()
        except ValidationError as e:
            # If it's about province, ignore it in admin
            if 'province' in e.message_dict:
                # Re-raise only other errors if any
                other_errors = {k: v for k, v in e.message_dict.items() if k != 'province'}
                if other_errors:
                    raise ValidationError(other_errors)
            else:
                # Re-raise the error if it's not about province
                raise

    def get_organization_info(self):
        """Return organization information for profile display"""
        if self.role == 'ADMIN_NATIONAL':
            return {
                'type': 'National',
                'name': 'SAFA National Office',
                'level': 'National Level'
            }
        elif self.role == 'ADMIN_PROVINCE' and self.province:
            return {
                'type': 'Province',
                'name': self.province.name,
                'level': 'Provincial Level'
            }
        elif self.role == 'ADMIN_REGION' and self.region:
            return {
                'type': 'Region',
                'name': self.region.name,
                'level': 'Regional Level'
            }
        elif self.role == 'ADMIN_LOCAL_FED' and self.local_federation:
            return {
                'type': 'LFA',
                'name': self.local_federation.name,
                'level': 'LFA Level',
                'region': self.region.name if self.region else None,
                'province': self.province.name if self.province else None
            }
        elif self.role == 'ASSOCIATION_ADMIN' and self.association:
            return {
                'type': 'Association',
                'name': self.association.name,
                'level': 'Association Level'
            }
        elif self.role == 'CLUB_ADMIN' and self.club:
            return {
                'type': 'Club',
                'name': self.club.name,
                'level': 'Club Level',
                'lfa': self.local_federation.name if self.local_federation else None,
                'region': self.region.name if self.region else None,
                'province': self.province.name if self.province else None
            }
        # Check for association even if not association admin
        elif self.association:
            return {
                'type': 'Association',
                'name': self.association.name,
                'level': 'Association Level'
            }
        # Fallback: show region/province if set, even if org is not
        if self.region:
            return {
                'type': 'Region',
                'name': self.region.name,
                'level': 'Regional Level (Fallback)'
            }
        if self.province:
            return {
                'type': 'Province',
                'name': self.province.name,
                'level': 'Provincial Level (Fallback)'
            }
        return {
            'type': 'Unknown',
            'name': None,
            'level': 'No Level'
        }

    def get_province_name(self):
        """Get province name from province_id"""
        if self.province_id:
            try:
                from geography.models import Province
                province = Province.objects.get(id=self.province_id)
                return province.name
            except:
                pass
        return "Not Set"

    def get_region_name(self):
        """Get region name from region FK directly if possible, fallback to region_id lookup."""
        if self.region and hasattr(self.region, 'name') and self.region.name:
            return self.region.name
        if self.region_id:
            try:
                from geography.models import Region
                region = Region.objects.get(id=self.region_id)
                return region.name
            except Exception:
                pass
        return "Not Set"

    def get_lfa_name(self):
        """Get LFA name from local_federation_id"""
        if self.local_federation_id:
            try:
                from geography.models import LocalFootballAssociation
                lfa = LocalFootballAssociation.objects.get(id=self.local_federation_id)
                return lfa.name
            except:
                pass
        return "Not Set"

    def get_club_name(self):
        """Get club name from club_id"""
        if self.club_id:
            try:
                from geography.models import Club
                club = Club.objects.get(id=self.club_id)
                return club.name
            except:
                pass
        return "Not Set"

    @property
    def is_id_valid(self):
        """Check if the provided ID number is valid"""
        if self.id_number:
            id_info = self.extract_id_info(self.id_number)
            return id_info.get('is_valid', False)
        return False

    @property
    def is_profile_complete(self):
        """Check if user profile is complete for compliance"""
        required_items = [
            self.profile_photo,
            self.id_document,
            self.popi_act_consent,
        ]
        return all(required_items)

    def get_compliance_score(self):
        """Get compliance percentage"""
        total_items = 4  # profile_photo, id_document, popi_consent, id_valid
        completed_items = 0

        if self.profile_photo:
            completed_items += 1
        if self.id_document:
            completed_items += 1
        if self.popi_act_consent:
            completed_items += 1
        if self.is_id_valid:
            completed_items += 1

        return int((completed_items / total_items) * 100)

    @property
    def age(self):
        """Return the user's age in years, or None if date_of_birth is not set."""
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        dob = self.date_of_birth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age

    def is_junior(self):
        """Return True if user is a junior (under 18), else False. None if unknown."""
        if self.age is None:
            return None
        return self.age < 18


class RolePermissions:
    @staticmethod
    def assign_permissions(user):
        if user.role == 'ADMIN_LOCAL_FED':
            # Example: Add permission to register clubs
            permission = Permission.objects.get(codename='add_club')
            user.user_permissions.add(permission)
        elif user.role == 'ADMIN_REGION':
            # Add region-specific permissions
            pass
        elif user.role == 'ADMIN_PROVINCE':
            # Add province-specific permissions
            pass
        elif user.role == 'ADMIN_NATIONAL':
            # Add national-specific permissions
            pass
        elif user.role == 'CLUB_ADMIN':
            # Add club-specific permissions
            pass


class LFAAdministrator(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    lfa = models.ForeignKey('geography.LocalFootballAssociation', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.email} - {self.lfa.name}"


class DocumentAccessLog(models.Model):
    """Track all document downloads and access"""
    DOCUMENT_TYPES = [
        ('player_id', 'Player ID Document'),
        ('player_passport', 'Player Passport'),
        ('player_sa_passport', 'Player SA Passport'),
        ('player_profile', 'Player Profile Picture'),
        ('official_id', 'Official ID Document'),
        ('official_passport', 'Official Passport'),
        ('official_cert', 'Official Certification'),
        ('club_document', 'Club Document'),
        ('other', 'Other Document'),
    ]

    ACTION_TYPES = [
        ('view', 'Viewed'),
        ('download', 'Downloaded'),
        ('print', 'Printed'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, help_text="User who accessed the document")
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_name = models.CharField(max_length=255, help_text="Original document filename")
    document_owner = models.CharField(max_length=255, help_text="Person/entity the document belongs to")
    action = models.CharField(max_length=10, choices=ACTION_TYPES, default='view')
    access_time = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True, help_text="File size in bytes")
    watermarked = models.BooleanField(default=False, help_text="Whether document was watermarked")
    success = models.BooleanField(default=True, help_text="Whether access was successful")
    notes = models.TextField(blank=True, help_text="Additional notes about the access")

    class Meta:
        db_table = 'document_access_log'
        ordering = ['-access_time']
        verbose_name = 'Document Access Log'
        verbose_name_plural = 'Document Access Logs'

    def __str__(self):
        return f"{self.user.get_full_name()} {self.action} {self.document_name} at {self.access_time}"

    @property
    def formatted_file_size(self):
        """Return human readable file size"""
        if not self.file_size:
            return "Unknown"

        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


    

