from django.contrib.auth.models import AbstractUser, BaseUserManager, Permission
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from typing import Any

from geography.models import (
    Club, Region, Association, LocalFootballAssociation,
    NationalFederation, MotherBody, Province
)


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
    ('ADMIN_NATIONAL_ACCOUNTS', _('National Accounts Administrator')),
    ('ADMIN_PROVINCE', _('Provincial Administrator')),
    ('ADMIN_REGION', _('Regional Administrator')),
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

class CustomUser(AbstractUser):
    # Remove the username field
    username = None

    # Required fields
    email = models.EmailField(_('email address'), unique=True)
    
    # Core Fields
    role = models.CharField(max_length=30, choices=ROLES, default='ADMIN_PROVINCE')
    
    # Add missing required validation
    first_name = models.CharField(_('first name'), max_length=150, blank=False)
    last_name = models.CharField(_('last name'), max_length=150, blank=False)

    # Identification Fields
    id_document_type = models.CharField(max_length=5, choices=DOCUMENT_TYPES, default='ID')
    id_number = models.CharField(max_length=13, unique=True, null=True, blank=True, help_text="South African ID Number")
    passport_number = models.CharField(max_length=25, unique=True, null=True, blank=True, help_text="Passport Number")
    id_number_other = models.CharField(max_length=25, null=True, blank=True, help_text="Other identification number")
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    # Profile and Document Fields
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    id_document = models.FileField(upload_to='id_documents/', null=True, blank=True)
    safa_id = models.CharField(max_length=5, unique=True, null=True, blank=True, help_text="Unique SAFA ID")
    fifa_id = models.CharField(max_length=7, unique=True, null=True, blank=True, help_text="Unique FIFA ID")
    country_code = models.CharField(max_length=3, default='ZAF')
    nationality = models.CharField(max_length=50, default='South African')
    popi_act_consent = models.BooleanField(default=False, help_text="Consent to POPI Act")

    # Membership Status Fields
    is_approved = models.BooleanField(default=False, help_text="Indicates if the user's registration has been approved by an admin.")
    membership_status = models.CharField(max_length=20, default='PENDING', choices=(
        ('PENDING', 'Pending Approval'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
        ('EXPIRED', 'Expired'),
    ))
    membership_activated_date = models.DateField(null=True, blank=True)
    registration_date = models.DateField(auto_now_add=True)

    # South African Passport Fields (for players/officials with dual IDs)
    has_sa_passport = models.BooleanField(default=False, help_text="Does the user have a South African passport?")
    sa_passport_number = models.CharField(max_length=25, unique=True, null=True, blank=True, help_text="South African Passport Number")
    sa_passport_document = models.FileField(upload_to='sa_passports/', null=True, blank=True, help_text="Scanned copy of SA Passport")
    sa_passport_expiry_date = models.DateField(null=True, blank=True)

    # Address Fields
    street_address = models.CharField(max_length=255, blank=True, null=True)
    suburb = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)

    # Organizational Relationships (Foreign Keys to Geography App)
    national_federation = models.ForeignKey('geography.NationalFederation', on_delete=models.SET_NULL, null=True, blank=True)
    province = models.ForeignKey('geography.Province', on_delete=models.SET_NULL, null=True, blank=True)
    region = models.ForeignKey('geography.Region', on_delete=models.SET_NULL, null=True, blank=True)
    local_federation = models.ForeignKey('geography.LocalFootballAssociation', on_delete=models.SET_NULL, null=True, blank=True)
    club = models.ForeignKey('geography.Club', on_delete=models.SET_NULL, null=True, blank=True)
    association = models.ForeignKey('geography.Association', on_delete=models.SET_NULL, null=True, blank=True)
    mother_body = models.ForeignKey('geography.MotherBody', on_delete=models.SET_NULL, null=True, blank=True)

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

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email

    def __str__(self):
        return self.get_full_name()

    @property
    def is_profile_complete(self):
        """Check if essential profile information is complete for approval."""
        # Basic checks for all users
        if not all([
            self.first_name, self.last_name, self.email,
            self.id_document_type, self.date_of_birth, self.gender,
            self.profile_picture, self.id_document, self.popi_act_consent
        ]):
            return False

        # Check ID/Passport based on type
        if self.id_document_type == 'ID' and not self.id_number:
            return False
        if self.id_document_type == 'PP' and not self.passport_number:
            return False

        # Role-specific checks
        if self.role == 'PLAYER' and not self.club:
            return False
        if self.role == 'OFFICIAL' and not self.association:
            return False
        
        # For admins, check if their organizational affiliation is set
        if self.role in ['ADMIN_PROVINCE', 'ADMIN_REGION', 'ADMIN_LOCAL_FED', 'CLUB_ADMIN', 'ASSOCIATION_ADMIN']:
            if self.organization_type.level == 'PROVINCE' and not self.province:
                return False
            if self.organization_type.level == 'REGION' and not self.region:
                return False
            if self.organization_type.level == 'LFA' and not self.local_federation:
                return False
            if self.organization_type.level == 'CLUB' and not self.club:
                return False
            if self.organization_type.level == 'ASSOCIATION' and not self.association:
                return False

        return True

    @property
    def payment_required(self):
        """Determine if a user's registration requires payment."""
        # Example logic: Players and Officials require payment, Admins do not.
        return self.role in ['PLAYER', 'OFFICIAL']

    def get_compliance_score(self):
        """Calculate a compliance score based on profile completeness and document uploads."""
        score = 0
        max_score = 100

        # Essential fields (30 points)
        if self.first_name and self.last_name and self.email: score += 10
        if self.date_of_birth and self.gender: score += 10
        if self.popi_act_consent: score += 10

        # Identification (30 points)
        if self.id_document_type == 'ID' and self.id_number: score += 15
        elif self.id_document_type == 'PP' and self.passport_number: score += 15
        if self.id_document: score += 15

        # Profile Picture (10 points)
        if self.profile_picture: score += 10

        # SAFA ID (10 points)
        if self.safa_id: score += 10

        # Organizational affiliation (20 points)
        if self.role == 'PLAYER' and self.club: score += 20
        elif self.role == 'OFFICIAL' and self.association: score += 20
        elif self.role in ['ADMIN_PROVINCE', 'ADMIN_REGION', 'ADMIN_LOCAL_FED', 'CLUB_ADMIN', 'ASSOCIATION_ADMIN']:
            if (self.organization_type.level == 'PROVINCE' and self.province) or \
               (self.organization_type.level == 'REGION' and self.region) or \
               (self.organization_type.level == 'LFA' and self.local_federation) or \
               (self.organization_type.level == 'CLUB' and self.club) or \
               (self.organization_type.level == 'ASSOCIATION' and self.association):
                score += 20

        return min(score, max_score) # Ensure score doesn't exceed max

    @staticmethod
    def extract_id_info(id_number):
        """Extracts date of birth and gender from a South African ID number."""
        if not id_number or not isinstance(id_number, str) or len(id_number) != 13 or not id_number.isdigit():
            return {'is_valid': False, 'error': 'Invalid ID number format.'}

        try:
            year_prefix = int(id_number[0:2])
            current_year_last_two_digits = timezone.now().year % 100

            # Determine full birth year (handle 19xx vs 20xx)
            if year_prefix <= current_year_last_two_digits:
                year = 2000 + year_prefix
            else:
                year = 1900 + year_prefix

            month = int(id_number[2:4])
            day = int(id_number[4:6])

            dob = timezone.datetime(year, month, day).date()

            gender_digit = int(id_number[6])
            gender = 'F' if gender_digit < 5 else 'M'

            return {'is_valid': True, 'date_of_birth': dob, 'gender': gender}
        except (ValueError, IndexError):
            return {'is_valid': False, 'error': 'Could not extract info from ID number.'}

    @property
    def member_profile(self):
        """Returns the associated Member object if it exists, otherwise None."""
        try:
            return self.member
        except Member.DoesNotExist:
            return None


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




