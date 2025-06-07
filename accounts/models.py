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
    ('ADMIN_FEDERATION', _('Federation Admin')),
    ('ADMIN_PROVINCE', _('Province Admin')),
    ('ADMIN_REGION', _('Region Admin')),
    ('ADMIN_LOCAL_FED', _('Local Federation Admin')),
    ('NATIONAL_ADMIN', _('National Administrator')),
    ('CLUB_ADMIN', _('Club Administrator')),
    ('PLAYER', _('Player')),
    ('REFEREE', _('Referee')),
    ('COACH', _('Coach')),
    ('EXECUTIVE', _('Exco Member')),
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
    role = models.CharField(max_length=20, choices=ROLES, default='PLAYER')
    name = models.CharField(max_length=50, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    surname = models.CharField(max_length=100, blank=True)
    alias = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)

    # Add country field to store country code
    country_code = models.CharField(max_length=3, default='ZAF', blank=True)

    # Identification
    id_number = models.CharField(
        max_length=20, 
        blank=True,
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

    # Comment out these problematic fields temporarily
    """
    # Admin-specific fields - use string references to avoid circular imports
    province = models.ForeignKey(
        'geography.Province',
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='province_admins'
    )
    
    region = models.ForeignKey(
        'geography.Region',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='region_admins'
    )
    
    local_federation = models.ForeignKey(
        'geography.LocalFootballAssociation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lfa_admins'
    )
    
    club = models.ForeignKey(
        'membership.Club',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='club_admins'
    )
    """
    
    # Instead use plain integer fields for now
    province_id = models.IntegerField(null=True, blank=True)
    region_id = models.IntegerField(null=True, blank=True)
    local_federation_id = models.IntegerField(null=True, blank=True)
    club_id = models.IntegerField(null=True, blank=True)

    # Specify the custom manager
    objects = CustomUserManager()

    # Set email as the USERNAME_FIELD
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        
    # FIXED: Removed problematic __init__ method
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.country = None  # This was causing issues

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
        """Override save method to validate ID number if it has changed"""
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

    def generate_safa_id(self):
        """Generate a unique 5-character uppercase alphanumeric code"""
        while True:
            code = get_random_string(length=5, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            if not CustomUser.objects.filter(safa_id=code).exists():
                self.safa_id = code
                break
    def fetch_fifa_id_from_api(self, api_key):
        # You would call the external API here
        # Example placeholder
        if not self.fifa_id:
            self.fifa_id = get_random_string(length=7, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            self.save()

    def generate_qr_code(self, size=200):
        """
        Generate a QR code for the user.
        Returns the QR code as a base64 encoded string that can be embedded in HTML.
        """
        try:
            import qrcode
            import base64
            from io import BytesIO

            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )

            # Data to encode in QR code
            data = {
                'id': str(self.id),
                'username': self.username,
                'name': f"{self.name} {self.surname}",
                'role': self.role,
                'safa_id': self.safa_id or '',
                'fifa_id': self.fifa_id or '',
            }

            # Add data to QR code
            qr.add_data(str(data))
            qr.make(fit=True)

            # Create an image from the QR code
            img = qr.make_image(fill_color="black", back_color="white")

            # Save the image to a BytesIO object
            buffer = BytesIO()
            img.save(buffer)

            # Encode the image as base64
            img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')

            return f"data:image/png;base64,{img_str}"
        except ImportError:
            # If qrcode is not installed, return None
            return None

class Membership(TimeStampedModel, ModelWithLogo):
    """Represents a membership relationship between a user and an organization"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='memberships')
    # Using generic relations to allow membership in different types of organizations
    membership_type = models.CharField(max_length=50)  # e.g., 'club', 'association', 'federation'
    address = models.CharField(max_length=255, blank=True)
    postal_address = models.CharField(max_length=255, blank=True)
    next_of_kin = models.CharField(max_length=100, blank=True)
    # Optional relationships - only one should be used based on membership_type
    club = models.ForeignKey(
        'geography.Club',
        on_delete=models.CASCADE,
        related_name='club_memberships',  # Changed from 'members'
        null=True,
        blank=True
    )
    association = models.ForeignKey(
        'geography.Association',
        on_delete=models.CASCADE,
        related_name='association_memberships',  # Changed from 'members'
        null=True,
        blank=True
    )
    # Best Practice: Consider models.SET_NULL if memberships should not be deleted when a federation/region is deleted.
    # related_name can be made more specific (e.g., 'memberships_in_national_federation') if 'members' is ambiguous
    # for the NationalFederation model or causes clashes.
    national_federation = models.ForeignKey(
        'geography.NationalFederation',
        on_delete=models.CASCADE,  # Consider models.SET_NULL or models.PROTECT based on desired data integrity.
        related_name='memberships', # Changed from 'members' for potentially better clarity.
        null=True,
        blank=True,
        verbose_name="National Federation"  # Added for better representation in forms/admin.
    )
    region = models.ForeignKey(  # PEP 8: Renamed from 'Region' to 'region'.
        'geography.Region',  # Using string literal for robustness (handles forward references/lazy loading).
        on_delete=models.CASCADE,  # Consider models.SET_NULL or models.PROTECT.
        related_name='memberships', # Changed from 'members' for potentially better clarity.
        null=True,
        blank=True,
        verbose_name="Region"  # Added for better representation in forms/admin.
    )
    local_football_association = models.ForeignKey(
        'geography.LocalFootballAssociation',
        on_delete=models.CASCADE,
        related_name='members',
        null=True,
        blank=True
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    # Add this field to your Membership model
    payment_confirmed = models.BooleanField(default=False)
    payment_date = models.DateTimeField(null=True, blank=True)  # Optional: track when payment was confirmed

    # For players
    player_category = models.CharField(max_length=3, choices=PLAYER_CATEGORIES, null=True, blank=True)
    jersey_number = models.PositiveSmallIntegerField(null=True, blank=True)
    position = models.CharField(max_length=50, blank=True)

    def __str__(self):
        org_name = ""
        if self.club:
            org_name = self.club.name
        elif self.association:
            org_name = self.association.name
        elif self.national_federation:
            org_name = self.national_federation.name

        return f"{self.user} - {org_name}"

    class Meta:
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'membership_type', 'club', 'association', 'national_federation'],
                name='unique_membership_combination'  # Descriptive name for the constraint
            )
        ]
    def save(self, *args, **kwargs):
        # Check if payment_confirmed changed from False to True
        if self.payment_confirmed and self.pk:
            # Get the original object to check if payment_confirmed changed
            original = Membership.objects.get(pk=self.pk)
            if not original.payment_confirmed:
                # Payment just got confirmed
                self._handle_payment_confirmation()
        # For new memberships where payment is confirmed immediately
        elif self.payment_confirmed and not self.pk:
            self._handle_payment_confirmation()
        super().save(*args, **kwargs)

    def _handle_payment_confirmation(self):
        """Handle actions when payment is confirmed"""
        from django.utils import timezone

        # Activate the user and membership
        self.user.is_active = True
        self.is_active = True

        # Generate SAFA ID only if user doesn't have one
        if not self.user.safa_id:
            self.user.generate_safa_id()

        # Set payment date if not already set
        if not self.payment_date:
            self.payment_date = timezone.now()

        # Save the user changes
        self.user.save()

    @property
    def membership_qr_code(self):
        """Generate QR code for membership card"""
        return self.user.generate_qr_code()

    @property  
    def ready_for_card_printing(self):
        """Check if membership is ready for card printing"""
        return (
            self.payment_confirmed and 
            self.is_active and 
            self.user.safa_id and
            self.user.is_active
        )



