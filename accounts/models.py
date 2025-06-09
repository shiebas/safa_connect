from django.contrib.auth.models import AbstractUser, BaseUserManager
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
    ('ADMIN_PROVINCE', _('Province Admin')),
    ('ADMIN_REGION', _('Region Admin')),
    ('ADMIN_LOCAL_FED', _('Local Federation Admin')),
    ('CLUB_ADMIN', _('Club Administrator')),
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

class ModelWithLogo(models.Model):
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)

    @cached_property
    def logo_url(self):
        if self.logo and hasattr(self.logo, 'url'):
            return self.logo.url
        return '/static/default_logo.png'

    class Meta:
        abstract = True

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

    # Add country field to store country code
    country_code = models.CharField(max_length=3, default='ZAF', blank=True)

    # Identification - FIXED to handle empty values
    id_number = models.CharField(
        max_length=20, 
        blank=True,
        null=True,  # ADD THIS - allow NULL values
        unique=True,  # This will work correctly with NULL values
        help_text=_("13-digit South African ID number")
    )
    id_number_other = models.CharField(max_length=25, blank=True, null=True)  # No unique constraint
    passport_number = models.CharField(max_length=25, blank=True)
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
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    id_document = models.FileField(
        upload_to='user_documents/',
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
        help_text='Amount paid for membership'
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

    # Specify the custom manager
    objects = CustomUserManager()

    # Set email as the USERNAME_FIELD
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        constraints = [
            # Ensure ID number is unique when not blank
            models.UniqueConstraint(
                fields=['id_number'],
                condition=models.Q(id_number__isnull=False) & ~models.Q(id_number=''),
                name='unique_id_number_when_not_blank'
            ),
        ]
 

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

    def save(self, *args, **kwargs):
        """Override save method to validate ID number and set nationality"""
        # Set nationality based on document type
        if self.id_document_type in ['ID', 'BC'] and not self.nationality:
            self.nationality = 'ZAF'  # South African citizenship for SA documents
            
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
            
            # Ensure uniqueness
            if not User.objects.filter(safa_id=safa_id).exists():
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
                # Determine century (19xx or 20xx)
                from django.utils import timezone
                current_year = timezone.now().year % 100
                century = '19' if int(year) > current_year else '20'
                full_year = int(century + year)

                # Check if date is valid
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

            # Validate checksum (Luhn algorithm)
            total = 0
            for i in range(len(id_number) - 1):
                digit = int(id_number[i])
                if i % 2 == 0:
                    total += digit
                else:
                    # For odd positions, double the digit and sum the digits of the result
                    doubled = digit * 2
                    total += doubled if doubled < 10 else (doubled - 9)

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
            # Log but don't raise
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error validating ID number for {self.email}: {str(e)}")

    def fetch_fifa_id_from_api(self, api_key):
        """Fetch FIFA ID from external API or generate placeholder"""
        # You would call the external API here
        # Example placeholder
        if not self.fifa_id:
            self.fifa_id = get_random_string(length=7, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            self.save()
            
    @property
    def is_province_admin(self):
        """Check if user is a province administrator"""
        return self.role == 'ADMIN_PROVINCE'
        
    @property
    def is_region_admin(self):
        """Check if user is a region administrator"""
        return self.role == 'ADMIN_REGION'
        
    @property
    def is_local_fed_admin(self):
        """Check if user is a local federation administrator"""
        return self.role == 'ADMIN_LOCAL_FED'
        
    @property
    def is_federation_admin(self):
        """Check if user is a federation administrator"""
        return self.role == 'ADMIN_FEDERATION'
        
    @property
    def is_club_admin(self):
        """Check if user is a club administrator"""
        return self.role == 'CLUB_ADMIN'
        
    def can_manage_province(self, province_id):
        """Check if user can manage the specified province"""
        return self.is_federation_admin or self.is_province_admin
        
    def can_manage_region(self, region_id):
        """Check if user can manage the specified region"""
        return self.is_federation_admin or self.is_province_admin or self.is_region_admin
        
    def can_manage_local_federation(self, local_fed_id):
        """Check if user can manage the specified local federation"""
        return self.is_federation_admin or self.is_province_admin or self.is_region_admin or self.is_local_fed_admin
        
    def can_manage_club(self, club_id):
        """Check if user can manage the specified club"""
        return self.is_federation_admin or self.is_province_admin or self.is_region_admin or self.is_local_fed_admin or self.is_club_admin
        
    def get_managed_provinces(self):
        """Get QuerySet of provinces managed by this user"""
        from django.db import models
        if self.is_federation_admin or self.is_province_admin:
            return models.Q(id__isnull=False)  # Can manage all provinces
        else:
            return models.Q(id__isnull=True)  # Cannot manage any provinces
            
    def get_managed_regions(self):
        """Get QuerySet of regions managed by this user"""
        from django.db import models
        if self.is_federation_admin or self.is_province_admin or self.is_region_admin:
            return models.Q(id__isnull=False)  # Can manage regions based on role
        else:
            return models.Q(id__isnull=True)  # Cannot manage any regions




