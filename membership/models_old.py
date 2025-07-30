from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from model_utils.models import TimeStampedModel
from django.conf import settings
from django.utils.crypto import get_random_string
import os
from geography.models import (
    ModelWithLogo,
    Province,
    Region,
    LocalFootballAssociation,
    Club as GeographyClub
)
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid
from decimal import Decimal, ROUND_HALF_UP


# Import utils functions conditionally to avoid import issues
try:
    from utils.qr_code_utils import generate_qr_code, get_member_qr_data
except ImportError:
    def generate_qr_code(data, size=200):
        return None
    def get_member_qr_data(member):
        return {}

# Constants for default images
DEFAULT_PROFILE_PICTURE = 'default_profile.png'
DEFAULT_LOGO = 'default_logo.png'


class SAFASeasonConfig(models.Model):
    """
    Configuration for SAFA seasons and fee structures
    Managed by NATIONAL_ADMIN_ACCOUNTS role
    """
    season_year = models.PositiveIntegerField(
        _("Season Year"), 
        unique=True,
        help_text=_("The year this season configuration applies to (e.g., 2025)")
    )
    
    # Season Dates
    season_start_date = models.DateField(
        _("Season Start Date"),
        help_text=_("When the season officially begins")
    )
    season_end_date = models.DateField(
        _("Season End Date"), 
        help_text=_("When the season officially ends")
    )
    
    # Tax Configuration
    vat_rate = models.DecimalField(
        _("VAT Rate"), 
        max_digits=5, 
        decimal_places=4, 
        default=Decimal('0.1500'),
        help_text=_("VAT rate as decimal (e.g., 0.1500 for 15%)")
    )
    
    # Payment Terms
    payment_due_days = models.PositiveIntegerField(
        _("Payment Due Days"),
        default=30,
        help_text=_("Number of days from invoice date until payment is due")
    )
    
    # Status
    is_active = models.BooleanField(
        _("Active Season"),
        default=False,
        help_text=_("Only one season can be active at a time")
    )
    
    is_renewal_season = models.BooleanField(
        _("Renewal Season"),
        default=False,
        help_text=_("Whether this is a renewal season (generates invoices for all entities)")
    )
    
    # Administrative
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_season_configs',
        help_text=_("Admin who created this season configuration")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("SAFA Season Configuration")
        verbose_name_plural = _("SAFA Season Configurations")
        ordering = ['-season_year']
    
    def __str__(self):
        status = "ACTIVE" if self.is_active else "INACTIVE"
        return f"SAFA Season {self.season_year} ({status})"
    
    def clean(self):
        super().clean()
        
        # Validate season dates
        if self.season_start_date and self.season_end_date:
            if self.season_start_date >= self.season_end_date:
                raise ValidationError(_("Season start date must be before end date"))
        
        # Validate VAT rate
        if self.vat_rate < 0 or self.vat_rate > 1:
            raise ValidationError(_("VAT rate must be between 0 and 1 (0% to 100%)"))
    
    def save(self, *args, **kwargs):
        # Ensure only one active season
        if self.is_active:
            SAFASeasonConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_season(cls):
        """Get the currently active season configuration"""
        return cls.objects.filter(is_active=True).first()
    
    @classmethod
    def get_current_season_year(cls):
        """Get current season year based on active config"""
        active_season = cls.get_active_season()
        if active_season:
            return active_season.season_year
        return timezone.now().year


class SAFAFeeStructure(models.Model):
    """
    Fee structure for different entity types and positions
    Configurable per season by NATIONAL_ADMIN_ACCOUNTS
    """
    ENTITY_TYPES = [
        ('ASSOCIATION', _('Association')),
        ('PROVINCE', _('Province')),
        ('REGION', _('Region')),
        ('LFA', _('Local Football Association')),
        ('CLUB', _('Club')),
        ('PLAYER_JUNIOR', _('Junior Player (Under 18)')),
        ('PLAYER_SENIOR', _('Senior Player (18+)')),
        ('OFFICIAL_REFEREE', _('Referee Official')),
        ('OFFICIAL_COACH', _('Coach Official')),
        ('OFFICIAL_GENERAL', _('General Official')),
        ('OFFICIAL_SECRETARY', _('Secretary Official')),
        ('OFFICIAL_TREASURER', _('Treasurer Official')),
        ('OFFICIAL_COMMITTEE', _('Committee Member')),
    ]
    
    season_config = models.ForeignKey(
        SAFASeasonConfig,
        on_delete=models.CASCADE,
        related_name='fee_structures'
    )
    
    entity_type = models.CharField(
        _("Entity Type"),
        max_length=30,
        choices=ENTITY_TYPES
    )
    
    annual_fee = models.DecimalField(
        _("Annual Fee (Excl. VAT)"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Annual membership fee excluding VAT in ZAR")
    )
    
    description = models.TextField(
        _("Fee Description"),
        blank=True,
        help_text=_("Description of what this fee covers")
    )
    
    is_pro_rata = models.BooleanField(
        _("Pro-rata Applicable"),
        default=True,
        help_text=_("Whether this fee can be calculated pro-rata for mid-season registrations")
    )
    
    minimum_fee = models.DecimalField(
        _("Minimum Fee (Excl. VAT)"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Minimum fee even for late registrations (optional)")
    )
    
    # Administrative
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_fee_structures'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("SAFA Fee Structure")
        verbose_name_plural = _("SAFA Fee Structures")
        unique_together = [('season_config', 'entity_type')]
        ordering = ['season_config', 'entity_type']
    
    def __str__(self):
        return f"{self.get_entity_type_display()} - R{self.annual_fee} ({self.season_config.season_year})"
    
    @classmethod
    def get_fee_for_entity(cls, entity_type, season_year=None):
        """Get fee for specific entity type in specific season"""
        if not season_year:
            season_config = SAFASeasonConfig.get_active_season()
        else:
            season_config = SAFASeasonConfig.objects.filter(season_year=season_year).first()
        
        if not season_config:
            return None
        
        fee_structure = cls.objects.filter(
            season_config=season_config,
            entity_type=entity_type
        ).first()
        
        return fee_structure


class Member(TimeStampedModel):
    """Enhanced Member model with SAFA integration"""
    MEMBER_TYPES = [
        ('JUNIOR', 'Junior Member (Under 18)'),
        ('SENIOR', 'Senior Member (18+)'),
        ('OFFICIAL', 'Club Official'),
        ('ADMIN', 'Administrator'),
    ]

    MEMBERSHIP_STATUS = [
        ('PENDING', 'Pending'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
        ('REJECTED', 'Rejected'),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    # User relationship
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='member_profile', 
        null=True, blank=True,
        help_text=_("The user account associated with this member profile")
    )

    # Identification Fields
    safa_id = models.CharField(
        _("SAFA ID"), 
        max_length=5, 
        unique=True,
        blank=True, null=True,
        help_text=_("5-digit unique SAFA identification number")
    )
    fifa_id = models.CharField(
        _("FIFA ID"), 
        max_length=7, 
        unique=True,
        blank=True, null=True,
        help_text=_("7-digit unique FIFA identification number")
    )
    id_number = models.CharField(
        _("ID Number"), 
        max_length=13, 
        blank=True,
        help_text=_("13-digit South African ID number")
    )
    passport_number = models.CharField(
        _('Passport Number'), 
        max_length=25, 
        blank=True, null=True, 
        help_text=_('Passport number for non-citizens')
    )
    gender = models.CharField(
        _("Gender"), 
        max_length=1, 
        choices=GENDER_CHOICES,
        blank=True, 
        help_text=_("Gender as per ID document")
    )

    # Personal Information
    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100)
    email = models.EmailField(_("Email Address"))
    phone_number = models.CharField(_("Phone Number"), max_length=20, blank=True)
    date_of_birth = models.DateField(_("Date of Birth"))
    member_type = models.CharField(
        _("Member Type"), 
        max_length=20, 
        choices=MEMBER_TYPES, 
        default='SENIOR', 
        blank=True, null=True
    )

    # Address Information
    street_address = models.CharField(_("Street Address"), max_length=255, blank=True)
    suburb = models.CharField(_("Suburb"), max_length=100, blank=True)
    city = models.CharField(_("City"), max_length=100, blank=True)
    state = models.CharField(_("State/Province"), max_length=100, blank=True)
    postal_code = models.CharField(_("Postal Code"), max_length=20, blank=True)
    country = models.CharField(_("Country"), max_length=100, blank=True)

    # SAFA Membership Information
    status = models.CharField(
        _("Membership Status"),
        max_length=20,
        choices=MEMBERSHIP_STATUS,
        default='PENDING'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_members'
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True)

    # Registration tracking
    registered_by_admin = models.BooleanField(
        _("Registered by Admin"),
        default=False,
        help_text=_("Whether this member was registered by a club administrator")
    )
    registering_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='registered_members',
        help_text=_("The club administrator who registered this member")
    )

    # Geography (for administrative purposes)
    province = models.ForeignKey(
        'geography.Province', 
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )
    region = models.ForeignKey(
        'geography.Region', 
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )
    lfa = models.ForeignKey(
        'geography.LocalFootballAssociation', 
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )
    club = models.ForeignKey(
        GeographyClub, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='club_members'
    )
    national_federation = models.ForeignKey(
        'geography.NationalFederation',
        on_delete=models.PROTECT,
        null=False, blank=False,
        default=1,
        help_text=_("The national federation this member belongs to")
    )
    association = models.ForeignKey(
        'geography.Association', 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='associated_members'
    )

    # Images
    profile_picture = models.ImageField(
        _("Profile Picture"),
        upload_to='member_profiles/',
        null=True, blank=True
    )

    # Emergency Contact
    emergency_contact = models.CharField(
        _("Emergency Contact"),
        max_length=100, blank=True
    )
    emergency_phone = models.CharField(
        _("Emergency Contact Phone"),
        max_length=20, blank=True
    )
    medical_notes = models.TextField(_("Medical Notes"), blank=True)

    # Document Fields for Player Registration
    id_document_type = models.CharField(
        max_length=2,
        choices=[('ID', 'SA ID'), ('PP', 'Passport')],
        default='ID',
        help_text=_('Type of identification document (SA ID or Passport)')
    )
    id_document = models.FileField(
        upload_to='documents/member_documents/',
        null=True, blank=True,
        help_text=_('Upload a scan/photo of the ID or passport')
    )

    # SA Passport fields
    has_sa_passport = models.BooleanField(
        _('Has SA Passport'),
        default=False,
        help_text=_('Whether the SA citizen member also has a valid SA passport for international travel')
    )
    sa_passport_number = models.CharField(
        _('SA Passport Number'),
        max_length=25,
        blank=True, null=True,
        help_text=_('South African passport number for citizens (for international travel)')
    )
    sa_passport_document = models.FileField(
        _('SA Passport Document'),
        upload_to='sa_passport_documents/',
        blank=True, null=True,
        help_text=_('Upload a copy of the SA passport')
    )
    sa_passport_expiry_date = models.DateField(
        _('SA Passport Expiry Date'),
        blank=True, null=True,
        help_text=_('Expiry date of the South African passport')
    )

    class Meta:
        verbose_name = _("Member")
        verbose_name_plural = _("Members")
        ordering = ['-created']
        permissions = [
            ("can_manage_club_members", "Can manage club members"),
            ("can_view_club_members", "Can view club members"),
            ("can_initiate_transfer", "Can initiate player transfers"),
            ("can_approve_transfer", "Can approve player transfers"),
            ("can_reject_transfer", "Can reject player transfers"),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_address_display(self):
        """Returns formatted full address"""
        address_parts = [
            self.street_address, self.suburb, self.city, 
            self.state, self.postal_code, self.country
        ]
        return ", ".join(part for part in address_parts if part)

    @property
    def profile_picture_url(self):
        """Returns URL for profile picture or default image"""
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return os.path.join(settings.STATIC_URL, DEFAULT_PROFILE_PICTURE)

    @property
    def logo_url(self):
        """Return default logo URL"""
        return os.path.join(settings.STATIC_URL, DEFAULT_LOGO)

    @property
    def is_visible_under_club(self):
        """Member is only visible under club if payment is confirmed"""
        if not self.club:
            return False
        # Check if any invoice is paid
        return self.invoices.filter(status='PAID').exists()

    @property
    def is_junior(self):
        """Check if member is under 18"""
        if self.date_of_birth:
            age = (timezone.now().date() - self.date_of_birth).days // 365
            return age < 18
        return self.member_type == 'JUNIOR'

    @property
    def age(self):
        """Calculate member's age"""
        if self.date_of_birth:
            return (timezone.now().date() - self.date_of_birth).days // 365
        return None

    @property
    def membership_card_ready(self):
        """Check if member is ready for membership card generation"""
        return (
            self.safa_id and
            self.status == 'ACTIVE' and
            self.profile_picture
        )

    def clean(self):
        super().clean()
        # Validate ID number if provided
        if self.id_number:
            self._validate_id_number()

        # Auto-detect member type based on age if not set
        if self.date_of_birth and not self.member_type:
            age = (timezone.now().date() - self.date_of_birth).days // 365
            self.member_type = 'JUNIOR' if age < 18 else 'SENIOR'

    def save(self, *args, **kwargs):
        # Auto-generate SAFA ID
        if not self.safa_id:
            self.generate_safa_id()

        # Validate before saving
        self.clean()

        super().save(*args, **kwargs)

    def approve_membership(self, approved_by):
        """Approve the member's SAFA registration"""
        self.status = 'ACTIVE'
        self.approved_by = approved_by
        self.approved_date = timezone.now()
        self.save()

    def reject_membership(self, rejected_by, reason):
        """Reject the member's SAFA registration"""
        self.status = 'REJECTED'
        self.rejection_reason = reason
        self.save()

    def generate_safa_id(self):
        """Generate a unique 5-character uppercase alphanumeric code"""
        while True:
            code = get_random_string(
                length=5,
                allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            )
            if not Member.objects.filter(safa_id=code).exists():
                self.safa_id = code
                break

    def generate_qr_code(self, size=200):
        """Generate QR code for member identification"""
        qr_data = get_member_qr_data(self)
        return generate_qr_code(qr_data, size)

    @property
    def qr_code(self):
        """Return QR code for member identification"""
        return self.generate_qr_code()

    def _validate_id_number(self):
        """Validate South African ID number format and content"""
        id_number = self.id_number.strip()

        if not id_number.isdigit() or len(id_number) != 13:
            raise ValidationError(_("ID number must be 13 digits."))

        try:
            # Extract and validate date of birth
            year = id_number[0:2]
            month = id_number[2:4]
            day = id_number[4:6]

            # Determine century (19xx or 20xx)
            current_year = timezone.now().year % 100
            century = '19' if int(year) > current_year else '20'
            full_year = int(century + year)

            # Validate date
            birth_date = timezone.datetime(full_year, int(month), int(day)).date()

            # Update date_of_birth if it doesn't match ID number
            if self.date_of_birth != birth_date:
                self.date_of_birth = birth_date

            # Extract and validate gender
            gender_digit = int(id_number[6:10])
            id_gender = 'M' if gender_digit >= 5000 else 'F'

            # Update gender if it doesn't match ID number
            if self.gender and self.gender != id_gender:
                raise ValidationError(_("ID number gender doesn't match the selected gender."))
            self.gender = id_gender

            # Validate citizenship digit (should be 0 or 1)
            citizenship = int(id_number[10])
            if citizenship not in [0, 1]:
                raise ValidationError(_("ID number citizenship digit must be 0 or 1."))

            # Validate checksum using Luhn algorithm
            digits = [int(d) for d in id_number]
            checksum = 0
            for i in range(len(digits)):
                if i % 2 == 0:
                    checksum += digits[i]
                else:
                    doubled = digits[i] * 2
                    checksum += doubled if doubled < 10 else (doubled - 9)
            if checksum % 10 != 0:
                raise ValidationError(_("ID number checksum is invalid."))
        except Exception as e:
            raise ValidationError(_("Invalid ID number: ") + str(e))

    def get_entity_type_for_fees(self):
        """Get the entity type for fee calculation"""
        if hasattr(self, 'player'):
            return 'PLAYER_JUNIOR' if self.is_junior else 'PLAYER_SENIOR'
        elif hasattr(self, 'official'):
            # Determine official type based on position
            if self.official.position and self.official.position.title:
                position_title = self.official.position.title.lower()
                if 'referee' in position_title:
                    return 'OFFICIAL_REFEREE'
                elif 'coach' in position_title:
                    return 'OFFICIAL_COACH'
                elif 'secretary' in position_title:
                    return 'OFFICIAL_SECRETARY'
                elif 'treasurer' in position_title:
                    return 'OFFICIAL_TREASURER'
                elif 'committee' in position_title:
                    return 'OFFICIAL_COMMITTEE'
            return 'OFFICIAL_GENERAL'
        return 'PLAYER_SENIOR'  # Default fallback


class Player(Member):
    """Player model represents a registered member who can play for clubs"""
    is_approved = models.BooleanField(
        _("Approved"), 
        default=False,
        help_text=_("Whether the player has been approved by an admin")
    )

    class Meta:
        verbose_name = _("Player")
        verbose_name_plural = _("Players")

    def save(self, *args, **kwargs):
        # Force member type for players
        if self.is_junior:
            self.member_type = 'JUNIOR'
        else:
            self.member_type = 'SENIOR'
        
        # Synchronize status with is_approved
        if self.is_approved:
            self.status = 'ACTIVE'
        else:
            self.status = 'PENDING'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name()} - {self.safa_id or 'No SAFA ID'}"


class JuniorMember(Member):
    """Junior members require guardian information"""
    guardian_name = models.CharField(_("Guardian Name"), max_length=100)
    guardian_email = models.EmailField(_("Guardian Email"))
    guardian_phone = models.CharField(_("Guardian Phone"), max_length=20)
    school = models.CharField(_("School"), max_length=100, blank=True)
    birth_certificate = models.ImageField(
        _("Birth Certificate"), 
        upload_to='documents/birth_certificates/', 
        null=True, blank=True
    )

    class Meta:
        verbose_name = _("Junior Member")
        verbose_name_plural = _("Junior Members")

    def clean(self):
        super().clean()
        # Force member type to be JUNIOR
        self.member_type = 'JUNIOR'

    def convert_to_senior(self):
        """Convert a junior member to a senior member when they turn 18"""
        if not self.is_junior:
            # Create a new Member instance with the same data
            senior_member = Member.objects.get(pk=self.pk)
            senior_member.member_type = 'SENIOR'
            senior_member.save()

            # Delete the JuniorMember instance but keep the base Member
            JuniorMember.objects.filter(pk=self.pk).delete()

            return senior_member
        return self


class Official(Member):
    """Official model represents club or association staff members"""
    is_approved = models.BooleanField(
        _("Approved"), 
        default=False,
        help_text=_("Whether the official has been approved by an admin")
    )

    # Position in the club or association
    position = models.ForeignKey(
        'accounts.Position', 
        on_delete=models.PROTECT,
        related_name='officials',
        help_text=_("Official's position or role in the club/association")
    )

    # Certification information
    certification_number = models.CharField(
        _("Certification Number"), 
        max_length=50, 
        blank=True, null=True,
        help_text=_("Certification or license number if applicable")
    )
    certification_document = models.FileField(
        _("Certification Document"), 
        upload_to='certification_documents/',
        blank=True, null=True,
        help_text=_("Upload proof of certification or qualification")
    )
    certification_expiry_date = models.DateField(
        _("Certification Expiry Date"), 
        blank=True, null=True,
        help_text=_("Expiry date of the certification or license")
    )

    # For referees
    referee_level = models.CharField(
        _("Referee Level"), 
        max_length=20, 
        blank=True, null=True,
        choices=[
            ('LOCAL', 'Local'),
            ('REGIONAL', 'Regional'),
            ('PROVINCIAL', 'Provincial'),
            ('NATIONAL', 'National'),
            ('INTERNATIONAL', 'International'),
        ],
        help_text=_("Level of referee qualification if applicable")
    )

    # Primary association (foreign key)
    primary_association = models.ForeignKey(
        'geography.Association',
        on_delete=models.SET_NULL,
        related_name='primary_officials',
        blank=True, null=True,
        help_text=_("Primary association this official belongs to")
    )

    # Link to referee associations (many-to-many)
    associations = models.ManyToManyField(
        'geography.Association',
        related_name='member_officials',
        blank=True,
        help_text=_("Referee or coaching associations this official belongs to")
    )

    class Meta:
        verbose_name = _("Official")
        verbose_name_plural = _("Officials")

    def __str__(self):
        position_name = self.position.title if self.position else "No Position"
        return f"{self.get_full_name()} - {position_name}"

    def save(self, *args, **kwargs):
        # Force member type
        self.member_type = 'OFFICIAL'

        # Sync associations between CustomUser and Official
        if hasattr(self, 'user') and self.user:
            if self.user.association and not self.primary_association:
                self.primary_association = self.user.association
            elif self.primary_association and not self.user.association:
                self.user.association = self.primary_association
                self.user.save(update_fields=['association'])

        super().save(*args, **kwargs)

        # Add primary association to associations M2M if it exists
        if self.primary_association:
            if not self.associations.filter(id=self.primary_association.id).exists():
                self.associations.add(self.primary_association)


class Vendor(TimeStampedModel):
    """Vendor model for suppliers, merchandise, etc."""
    name = models.CharField(_("Vendor Name"), max_length=200)
    email = models.EmailField(_("Email"), blank=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    address = models.TextField(_("Address"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    logo = models.ImageField(
        _("Logo"), 
        upload_to='vendor_logos/', 
        blank=True, null=True
    )
    
    class Meta:
        verbose_name = _("Vendor")
        verbose_name_plural = _("Vendors")
        ordering = ['name']
    
    def __str__(self):
        return self.name


# Replace your Invoice class with this corrected version
class Invoice(TimeStampedModel):
    """
    Comprehensive Invoice model with VAT compliance and SAFA integration
    Combines the best of both original models
    """
    INVOICE_STATUS = [
        ('DRAFT', _('Draft')),
        ('PENDING', _('Pending Payment')),
        ('PARTIALLY_PAID', _('Partially Paid')),
        ('PAID', _('Fully Paid')),
        ('OVERDUE', _('Overdue')),
        ('CANCELLED', _('Cancelled')),
        ('DISPUTED', _('Disputed')),
    ]
    
    INVOICE_TYPES = [
        ('REGISTRATION', _('Registration Fee')),
        ('ANNUAL_FEE', _('Annual Membership Fee')),
        ('RENEWAL', _('Season Renewal')),
        ('MEMBERSHIP', _('Membership Fee')),
        ('EVENT', _('Event Fee/Ticket')),
        ('TRANSFER_FEE', _('Transfer Fee')),
        ('PENALTY', _('Penalty/Fine')),
        ('MERCHANDISE', _('Merchandise Order')),
        ('OTHER', _('Other')),
    ]
    
    # Unique identifiers
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invoice_number = models.CharField(
        _("Invoice Number"), 
        max_length=50, 
        unique=True, 
        blank=True
    )
    
    # Season reference for SAFA compliance
    season_config = models.ForeignKey(
        SAFASeasonConfig,
        on_delete=models.PROTECT,
        related_name='invoices',
        null=True, blank=True,
        help_text=_("Season this invoice belongs to (for SAFA fees)")
    )
    
    # Basic invoice info
    status = models.CharField(
        _("Status"), 
        max_length=20, 
        choices=INVOICE_STATUS, 
        default='PENDING'
    )
    invoice_type = models.CharField(
        _("Invoice Type"), 
        max_length=20, 
        choices=INVOICE_TYPES, 
        default='OTHER'
    )
    
    # Member relationships
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='invoices',
        null=True, blank=True,
        help_text=_("Member this invoice is for")
    )
    
    # Specific member type relationships
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='player_invoices',
        null=True, blank=True,
        help_text=_("Player this invoice is for (if player registration)")
    )
    
    official = models.ForeignKey(
        Official,
        on_delete=models.CASCADE,
        related_name='official_invoices',
        null=True, blank=True,
        help_text=_("Official this invoice is for (if official registration)")
    )
    
    # Organization relationships
    club = models.ForeignKey(
        GeographyClub,
        on_delete=models.CASCADE,
        related_name='invoices',
        null=True, blank=True
    )
    
    association = models.ForeignKey(
        'geography.Association',
        on_delete=models.CASCADE,
        related_name='invoices',
        null=True, blank=True,
        help_text=_("Association this invoice is for (e.g., LFA, Region)")
    )
    
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text=_("Vendor associated with this invoice (if applicable)")
    )
    
    # Generic foreign key for maximum flexibility
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        null=True, blank=True,
        help_text=_("Type of organization (Club, LFA, etc.)")
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Financial details (VAT compliant)
    subtotal = models.DecimalField(
        _("Subtotal (Excl. VAT)"), 
        max_digits=12, 
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Total amount excluding VAT")
    )
    
    vat_rate = models.DecimalField(
        _("VAT Rate"), 
        max_digits=5, 
        decimal_places=4, 
        default=Decimal('0.1500'),
        help_text=_("VAT rate applied (e.g., 0.1500 for 15%)")
    )
    
    vat_amount = models.DecimalField(
        _("VAT Amount"), 
        max_digits=12, 
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("VAT amount calculated")
    )
    
    total_amount = models.DecimalField(
        _("Total Amount (Incl. VAT)"), 
        max_digits=12, 
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Total amount including VAT")
    )
    
    # Payment tracking
    paid_amount = models.DecimalField(
        _("Amount Paid"), 
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    
    outstanding_amount = models.DecimalField(
        _("Outstanding Amount"), 
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    
    # Dates
    issue_date = models.DateField(_("Issue Date"), default=timezone.now)
    due_date = models.DateField(_("Due Date"), null=True, blank=True)
    payment_date = models.DateTimeField(_("Payment Date"), null=True, blank=True)
    
    # Payment details
    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True)
    payment_reference = models.CharField(
        _("Payment Reference"), 
        max_length=100, 
        blank=True,
        help_text=_("Reference number for the payment")
    )
    
    # Pro-rata information for SAFA fees
    is_pro_rata = models.BooleanField(
        _("Pro-rata Invoice"), 
        default=False,
        help_text=_("Whether this invoice was calculated pro-rata")
    )
    pro_rata_months = models.PositiveIntegerField(
        _("Pro-rata Months"), 
        null=True, blank=True,
        help_text=_("Number of months for pro-rata calculation")
    )
    
    # Administrative
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='issued_invoices',
        null=True, blank=True
    )
    
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        ordering = ['-issue_date', '-created']
    
    def __str__(self):
        prefix = "SAFA" if self.season_config else "INV"
        return f"{prefix}-{self.invoice_number} - R{self.total_amount}"
    
    def save(self, *args, **kwargs):
        # Generate invoice number if not set
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        
        # Set VAT rate from season config if available
        if self.season_config and not self.vat_rate:
            self.vat_rate = self.season_config.vat_rate
        
        # Calculate totals from line items or use existing values
        if not self.subtotal and self.items.exists():
            self.recalculate_totals()
        else:
            self.calculate_totals()
        
        # Set due date if not set
        if not self.due_date:
            from datetime import timedelta
            if self.season_config:
                days = self.season_config.payment_due_days
            else:
                days = 30
            self.due_date = self.issue_date + timedelta(days=days)
        
        # Calculate outstanding amount
        self.outstanding_amount = self.total_amount - self.paid_amount
        
        # Update status based on payment
        self.update_payment_status()
        
        super().save(*args, **kwargs)
    
    # ===== EXISTING METHODS =====
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        if self.season_config:
            year = self.season_config.season_year
            prefix = f"SAFA{year}"
        else:
            year = timezone.now().year
            prefix = f"INV{year}"
        
        import random
        import string
        while True:
            suffix = ''.join(random.choices(string.digits, k=6))
            number = f"{prefix}{suffix}"
            if not Invoice.objects.filter(invoice_number=number).exists():
                return number
    
    def calculate_totals(self):
        """Calculate VAT and total amounts from subtotal"""
        if self.subtotal:
            self.vat_amount = (self.subtotal * self.vat_rate).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            self.total_amount = self.subtotal + self.vat_amount
    
    def recalculate_totals(self):
        """Recalculate totals from line items"""
        items = self.items.all()
        self.subtotal = sum(item.sub_total for item in items)
        self.calculate_totals()
        
        # Update without triggering save signal recursion
        Invoice.objects.filter(pk=self.pk).update(
            subtotal=self.subtotal,
            vat_amount=self.vat_amount,
            total_amount=self.total_amount
        )
    
    def update_payment_status(self):
        """Update invoice status based on payment amount"""
        if self.paid_amount >= self.total_amount:
            self.status = 'PAID'
            if not self.payment_date:
                self.payment_date = timezone.now()
        elif self.paid_amount > 0:
            self.status = 'PARTIALLY_PAID'
        elif self.due_date and self.due_date < timezone.now().date() and self.status == 'PENDING':
            self.status = 'OVERDUE'
    
    def add_payment(self, amount, payment_method='', payment_reference='', processed_by=None):
        """Add a payment to this invoice"""
        amount = Decimal(str(amount))
        
        # Create payment record
        payment = InvoicePayment.objects.create(
            invoice=self,
            amount=amount,
            payment_method=payment_method,
            payment_reference=payment_reference,
            processed_by=processed_by
        )
        
        # Update invoice
        self.paid_amount += amount
        self.payment_method = payment_method
        self.payment_reference = payment_reference
        
        self.save()
        
        # Trigger activation if fully paid
        if self.status == 'PAID':
            self.activate_member()
        
        return payment
    
    def activate_member(self):
        """Activate member/player/official when invoice is fully paid"""
        if self.player:
            self.player.is_approved = True
            self.player.status = 'ACTIVE'
            self.player.save()
        elif self.official:
            self.official.is_approved = True
            self.official.status = 'ACTIVE'
            self.official.save()
        elif self.member:
            self.member.status = 'ACTIVE'
            self.member.save()
    
    def mark_as_paid(self):
        """Mark invoice as paid manually"""
        if self.status != 'PAID':
            self.status = 'PAID'
            self.payment_date = timezone.now()
            self.paid_amount = self.total_amount
            self.outstanding_amount = Decimal('0.00')
            self.save()
            self.activate_member()
    
    # ===== PROPERTIES =====
    @property
    def is_paid(self):
        """Check if invoice is fully paid"""
        return self.status == 'PAID'
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        return self.status == 'OVERDUE' or (
            self.status in ['PENDING', 'PARTIALLY_PAID'] and 
            self.due_date and self.due_date < timezone.now().date()
        )
    
    @property
    def payment_percentage(self):
        """Calculate payment percentage"""
        if self.total_amount > 0:
            return (self.paid_amount / self.total_amount * 100).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        return Decimal('0.00')
    
    # ===== NEW UNIVERSAL METHODS =====
    def get_related_member(self):
        """Get the member associated with this invoice regardless of type"""
        if self.player:
            return self.player
        elif self.official:
            return self.official
        elif self.member:
            return self.member
        return None

    def get_member_display_name(self):
        """Get display name for the member associated with this invoice"""
        member = self.get_related_member()
        if member:
            return member.get_full_name()
        return "Unknown Member"

    def get_member_type_display(self):
        """Get the type of member for display purposes"""
        if self.player:
            return "Player"
        elif self.official:
            return "Official"
        elif self.member:
            return "Member"
        return "Unknown"

    def activate_related_member(self):
        """Activate the member associated with this invoice when payment is complete"""
        member = self.get_related_member()
        if member:
            member.status = 'ACTIVE'
            if hasattr(member, 'is_approved'):
                member.is_approved = True
            member.save()
            return True
        return False

    @property
    def is_member_visible_under_club(self):
        """Check if the member should be visible under their club (payment confirmed)"""
        member = self.get_related_member()
        if not member or not member.club:
            return False
        return self.status == 'PAID'
    
    # ===== CLASS METHODS =====
    @classmethod
    def create_safa_registration_invoice(cls, member, season_config=None):
        """Create a SAFA registration invoice for a member"""
        if not season_config:
            season_config = SAFASeasonConfig.get_active_season()
        
        if not season_config:
            raise ValidationError(_("No active SAFA season configuration found"))
        
        # Determine entity type and get fee
        entity_type = member.get_entity_type_for_fees()
        fee_structure = SAFAFeeStructure.get_fee_for_entity(
            entity_type, 
            season_config.season_year
        )
        
        if not fee_structure:
            raise ValidationError(
             *("No fee structure found for %(entity*type)s in season %(year)s") % {
             'entity_type': entity_type,
            'year': season_config.season_year

            }
        )
        
        # Create invoice with correct member assignment
        invoice_data = {
            'season_config': season_config,
            'invoice_type': 'REGISTRATION',
            'subtotal': fee_structure.annual_fee,
            'vat_rate': season_config.vat_rate,
        }
        
        # Assign the correct member relationship
        if isinstance(member, Player):
            invoice_data['player'] = member
        elif isinstance(member, Official):
            invoice_data['official'] = member
        else:
            invoice_data['member'] = member
        
        # Create the invoice
        invoice = cls.objects.create(**invoice_data)
        
        # Create line item
        InvoiceItem.objects.create(
            invoice=invoice,
            description=f"SAFA Registration - {fee_structure.get_entity_type_display()}",
            quantity=1,
            unit_price=fee_structure.annual_fee
        )
        
        return invoice

    @classmethod
    def create_universal_invoice(cls, member_instance, amount, descriptions, invoice_type='MEMBERSHIP'):
        """
        Universal invoice creation method that handles all member types
        """
        from decimal import Decimal
        
        # Prepare invoice data
        invoice_data = {
            'subtotal': Decimal(str(amount)),
            'status': 'PENDING',
            'invoice_type': invoice_type,
            'due_date': timezone.now().date() + timezone.timedelta(days=30)
        }
        
        # Set the appropriate member relationship
        if isinstance(member_instance, Player):
            invoice_data['player'] = member_instance
        elif isinstance(member_instance, Official):
            invoice_data['official'] = member_instance
        else:
            invoice_data['member'] = member_instance
        
        # Add club if available
        if hasattr(member_instance, 'club') and member_instance.club:
            invoice_data['club'] = member_instance.club
        
        # Add season config if available
        season_config = SAFASeasonConfig.get_active_season()
        if season_config:
            invoice_data['season_config'] = season_config
            invoice_data['vat_rate'] = season_config.vat_rate
        
        # Create the invoice
        invoice = cls.objects.create(**invoice_data)
        
        # Create invoice items
        if isinstance(descriptions, list):
            unit_price = Decimal(str(amount)) / len(descriptions)
            for desc in descriptions:
                InvoiceItem.objects.create(
                    invoice=invoice,
                    description=desc,
                    quantity=1,
                    unit_price=unit_price
                )
        else:
            InvoiceItem.objects.create(
                invoice=invoice,
                description=descriptions,
                quantity=1,
                unit_price=Decimal(str(amount))
            )
        
        return invoice
class InvoiceItem(models.Model):
    """Individual line items for invoices"""
    invoice = models.ForeignKey(
        Invoice, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    description = models.CharField(_("Description"), max_length=200)
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    unit_price = models.DecimalField(
        _("Unit Price (Excl. VAT)"), 
        max_digits=10, 
        decimal_places=2
    )
    
    class Meta:
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")
    
    def __str__(self):
        return f"{self.description} (x{self.quantity})"
    
    @property
    def sub_total(self):
        """Calculate subtotal for this line item"""
        quantity = self.quantity if self.quantity is not None else 0
        unit_price = self.unit_price if self.unit_price is not None else Decimal('0.00')
        return quantity * unit_price
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Trigger invoice recalculation
        if self.invoice_id:
            self.invoice.recalculate_totals()


class InvoicePayment(TimeStampedModel):
    """Track individual payments against invoices"""
    PAYMENT_METHODS = [
        ('EFT', _('Electronic Funds Transfer')),
        ('CASH', _('Cash')),
        ('CARD', _('Credit/Debit Card')),
        ('CHEQUE', _('Cheque')),
        ('ONLINE', _('Online Payment')),
        ('MOBILE', _('Mobile Payment')),
        ('OTHER', _('Other')),
    ]
    
    invoice = models.ForeignKey(
        Invoice, 
        on_delete=models.CASCADE, 
        related_name='payments'
    )
    
    amount = models.DecimalField(
        _("Payment Amount"), 
        max_digits=12, 
        decimal_places=2
    )
    
    payment_date = models.DateTimeField(_("Payment Date"), default=timezone.now)
    payment_method = models.CharField(
        _("Payment Method"), 
        max_length=20, 
        choices=PAYMENT_METHODS
    )
    payment_reference = models.CharField(
        _("Payment Reference"), 
        max_length=100, 
        blank=True
    )
    
    # Processing details
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='processed_payments'
    )
    
    notes = models.TextField(_("Payment Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Invoice Payment")
        verbose_name_plural = _("Invoice Payments")
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment R{self.amount} - {self.invoice.invoice_number}"


class ClubRegistration(TimeStampedModel):
    """Represents a member's registration with a specific club after SAFA approval"""
    REGISTRATION_STATUS = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
    ]

    member = models.OneToOneField(
        Member, 
        on_delete=models.CASCADE, 
        related_name='club_registration'
    )
    club = models.ForeignKey(
        GeographyClub, 
        on_delete=models.CASCADE, 
        related_name='member_registrations'
    )
    registration_date = models.DateField(default=timezone.now)
    status = models.CharField(
        max_length=20, 
        choices=REGISTRATION_STATUS, 
        default='PENDING'
    )
    position = models.CharField(max_length=50, blank=True)
    jersey_number = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Club Registration")
        verbose_name_plural = _("Club Registrations")
        unique_together = ('member', 'club')

    def __str__(self):
        return f"{self.member.get_full_name()} - {self.club.name}"

    def clean(self):
        super().clean()
        # Ensure member is approved before club registration
        if self.member.status != 'ACTIVE':
            raise ValidationError(_("Only approved SAFA members can register with clubs"))


class PlayerClubRegistration(TimeStampedModel):
    """Represents a player's registration with a specific club"""
    POSITION_CHOICES = [
        ('GK', 'Goalkeeper'),
        ('DF', 'Defender'),
        ('MF', 'Midfielder'),
        ('FW', 'Forward'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
        ('TRANSFERRED', 'Transferred'),
    ]

    player = models.ForeignKey(
        Player, 
        on_delete=models.CASCADE,
        related_name='club_registrations'
    )
    club = models.ForeignKey(
        GeographyClub, 
        on_delete=models.CASCADE,
        related_name='player_registrations'
    )
    
    # Registration Details
    registration_date = models.DateField(_("Registration Date"), default=timezone.now)
    status = models.CharField(
        _("Status"), 
        max_length=20,
        choices=STATUS_CHOICES, 
        default='PENDING'
    )
    expiry_date = models.DateField(_("Registration Expiry"), null=True, blank=True)

    # Playing Details
    position = models.CharField(
        _("Position"), 
        max_length=2,
        choices=POSITION_CHOICES, 
        blank=True
    )
    jersey_number = models.PositiveIntegerField(
        _("Jersey Number"),
        blank=True, null=True
    )
    
    # Physical Attributes
    height = models.DecimalField(
        _("Height (cm)"), 
        max_digits=5,
        decimal_places=2, 
        blank=True, null=True
    )
    weight = models.DecimalField(
        _("Weight (kg)"), 
        max_digits=5,
        decimal_places=2, 
        blank=True, null=True
    )

    # Additional Information
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Player Club Registration")
        verbose_name_plural = _("Player Club Registrations")
        ordering = ['-registration_date']
        constraints = [
            models.UniqueConstraint(
                fields=['player', 'club'],
                name='unique_active_player_registration',
                condition=models.Q(status='ACTIVE')
            )
        ]

    def __str__(self):
        return f"{self.player.get_full_name()} - {self.club.name}"

    def clean(self):
        super().clean()
        # Ensure player doesn't have another active registration
        if self.status == 'ACTIVE':
            existing = PlayerClubRegistration.objects.filter(
                player=self.player,
                status='ACTIVE'
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(_(
                    "Player already has an active registration with another club. "
                    "Please transfer or deactivate the existing registration first."
                ))


class Transfer(TimeStampedModel):
    """Represents a player transfer between clubs"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]

    player = models.ForeignKey(
        Player, 
        on_delete=models.CASCADE,
        related_name='transfers'
    )
    from_club = models.ForeignKey(
        GeographyClub, 
        on_delete=models.CASCADE,
        related_name='transfers_out'
    )
    to_club = models.ForeignKey(
        GeographyClub, 
        on_delete=models.CASCADE,
        related_name='transfers_in'
    )

    # Transfer Details
    request_date = models.DateField(_("Request Date"), default=timezone.now)
    effective_date = models.DateField(_("Effective Date"), null=True, blank=True)
    status = models.CharField(
        _("Status"), 
        max_length=20,
        choices=STATUS_CHOICES, 
        default='PENDING'
    )
    transfer_fee = models.DecimalField(
        _("Transfer Fee (ZAR)"), 
        max_digits=10,
        decimal_places=2, 
        default=0,
        help_text=_("Transfer fee amount in ZAR (South African Rand)")
    )
    reason = models.TextField(_("Transfer Reason"), blank=True)

    # Approval Details
    approved_by = models.ForeignKey(
        Member, 
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_transfers'
    )
    approved_date = models.DateTimeField(_("Approval Date"), null=True, blank=True)
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True)

    class Meta:
        verbose_name = _("Player Transfer")
        verbose_name_plural = _("Player Transfers")
        ordering = ['-request_date']
        permissions = [
            ("can_initiate_transfer", "Can initiate player transfers"),
            ("can_approve_transfer", "Can approve player transfers"),
            ("can_reject_transfer", "Can reject player transfers"),
            ("can_view_transfer", "Can view player transfers"),
        ]

    def __str__(self):
        return f"{self.player.get_full_name()} - {self.from_club.name} to {self.to_club.name}"

    def clean(self):
        super().clean()
        if self.from_club == self.to_club:
            raise ValidationError(_("Cannot transfer player to the same club."))

        # Check player's status
        if self.player.status in ['INACTIVE', 'SUSPENDED']:
            raise ValidationError(_(
                "Player cannot apply for transfer while their membership status is %(status)s."
            ) % {'status': self.player.get_status_display()})

        # Check if player is registered with from_club
        current_registration = PlayerClubRegistration.objects.filter(
            player=self.player,
            club=self.from_club,
            status='ACTIVE'
        ).first()

        if not current_registration:
            raise ValidationError(_("Player is not actively registered with the source club."))

        # Check for pending transfers
        pending_transfer = Transfer.objects.filter(
            player=self.player,
            status='PENDING'
        ).exclude(pk=self.pk).first()

        if pending_transfer:
            raise ValidationError(_("Player already has a pending transfer."))

    def approve(self, approved_by):
        """Approve the transfer and update registrations"""
        if self.status != 'PENDING':
            raise ValidationError(_("Only pending transfers can be approved."))

        with transaction.atomic():
            # Deactivate current registration
            PlayerClubRegistration.objects.filter(
                player=self.player,
                club=self.from_club,
                status='ACTIVE'
            ).update(status='TRANSFERRED')

            # Create new registration with to_club
            PlayerClubRegistration.objects.create(
                player=self.player,
                club=self.to_club,
                status='ACTIVE',
                registration_date=timezone.now().date()
            )

            # Update transfer record
            self.status = 'APPROVED'
            self.approved_by = approved_by
            self.approved_date = timezone.now()
            self.effective_date = timezone.now().date()
            self.save()

    def reject(self, rejected_by, reason):
        """Reject the transfer"""
        if self.status != 'PENDING':
            raise ValidationError(_("Only pending transfers can be rejected."))

        self.status = 'REJECTED'
        self.approved_by = rejected_by
        self.approved_date = timezone.now()
        self.rejection_reason = reason
        self.save()


class TransferAppeal(TimeStampedModel):
    """Represents an appeal against a rejected transfer"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('UPHELD', 'Upheld'),
        ('DISMISSED', 'Dismissed'),
        ('WITHDRAWN', 'Withdrawn'),
        ('ESCALATED', 'Escalated to Federation'),
        ('FEDERATION_APPROVED', 'Approved by Federation'),
        ('FEDERATION_REJECTED', 'Rejected by Federation'),
    ]

    transfer = models.OneToOneField(
        Transfer,
        on_delete=models.CASCADE,
        related_name='appeal'
    )
    submitted_by = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='submitted_appeals'
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    appeal_reason = models.TextField(_("Appeal Reason"))
    supporting_document = models.FileField(
        _("Supporting Document"),
        upload_to='transfer_appeals/',
        null=True, blank=True
    )
    reviewed_by = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_appeals'
    )
    review_date = models.DateTimeField(_("Review Date"), null=True, blank=True)
    review_notes = models.TextField(_("Review Notes"), blank=True)
    appeal_submission_date = models.DateTimeField(
        _("Appeal Submission Date"),
        default=timezone.now
    )
    federation_reviewer = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='federation_reviewed_appeals'
    )
    federation_review_date = models.DateTimeField(
        _("Federation Review Date"),
        null=True, blank=True
    )
    federation_review_notes = models.TextField(
        _("Federation Review Notes"),
        blank=True
    )
    requires_federation_approval = models.BooleanField(
        _("Requires Federation Approval"),
        default=False,
        help_text=_("If true, the appeal must be approved by the National Federation")
    )

    class Meta:
        verbose_name = _("Transfer Appeal")
        verbose_name_plural = _("Transfer Appeals")
        ordering = ['-appeal_submission_date']
        permissions = [
            ("can_review_appeals", "Can review transfer appeals"),
            ("can_submit_appeals", "Can submit transfer appeals"),
            ("can_review_federation_appeals", "Can review federation-level appeals"),
        ]

    def __str__(self):
        return f"Appeal for {self.transfer}"

    def clean(self):
        super().clean()
        # Only rejected transfers can be appealed
        if self.transfer.status != 'REJECTED':
            raise ValidationError(_("Only rejected transfers can be appealed."))

        # Check if appeal already exists
        if (TransferAppeal.objects.filter(transfer=self.transfer)
                                .exclude(pk=self.pk).exists()):
            raise ValidationError(_("An appeal already exists for this transfer."))

    def uphold(self, reviewed_by, notes=''):
        """Uphold the appeal and either approve the transfer or escalate to federation"""
        if self.status != 'PENDING':
            raise ValidationError(_("Only pending appeals can be reviewed."))

        with transaction.atomic():
            if self.requires_federation_approval:
                self.status = 'ESCALATED'
                self.reviewed_by = reviewed_by
                self.review_date = timezone.now()
                self.review_notes = notes
                self.save()
            else:
                self.status = 'UPHELD'
                self.reviewed_by = reviewed_by
                self.review_date = timezone.now()
                self.review_notes = notes
                self.save()
                # Approve the transfer
                self.transfer.approve(reviewed_by)

    def federation_review(self, federation_reviewer, approved, notes=''):
        """Review the appeal at federation level"""
        if self.status != 'ESCALATED':
            raise ValidationError(_("Only escalated appeals can be reviewed by federation."))

        with transaction.atomic():
            if approved:
                self.status = 'FEDERATION_APPROVED'
                # Approve the transfer
                self.transfer.approve(federation_reviewer)
            else:
                self.status = 'FEDERATION_REJECTED'

            self.federation_reviewer = federation_reviewer
            self.federation_review_date = timezone.now()
            self.federation_review_notes = notes
            self.save()


class Membership(models.Model):
    """Enhanced Membership model linking members to clubs"""
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    club = models.ForeignKey(GeographyClub, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', _('Active')),
            ('INACTIVE', _('Inactive')),
            ('SUSPENDED', _('Suspended')),
        ],
        default='ACTIVE'
    )

    class Meta:
        verbose_name = _('Membership')
        verbose_name_plural = _('Memberships')
        unique_together = ('member', 'club', 'start_date')

    def __str__(self):
        return f"{self.member} - {self.club}"


class MembershipApplication(models.Model):
    """Application for club membership"""
    member = models.ForeignKey(
        Member, 
        on_delete=models.CASCADE, 
        related_name='applications', 
        null=True, blank=True
    )
    club = models.ForeignKey(
        GeographyClub, 
        on_delete=models.CASCADE, 
        related_name='membership_applications'
    )
    signature = models.ImageField(upload_to='signatures/')
    date_signed = models.DateField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='PENDING'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, blank=True, 
        on_delete=models.SET_NULL, 
        related_name='reviewed_applications'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('Membership Application')
        verbose_name_plural = _('Membership Applications')

    def __str__(self):
        return f"Application: {self.member} to {self.club} ({self.status})"


class ClubWithSafaID(GeographyClub):
    """
    Proxy model to add SAFA ID functionality to clubs from geography app
    without modifying the original model's DB table.
    """
    class Meta:
        proxy = True
        verbose_name = _("Club with SAFA ID")
        verbose_name_plural = _("Clubs with SAFA ID")

    def generate_safa_id(self):
        """Generate a unique 5-character uppercase alphanumeric code for club"""
        if not hasattr(self, 'safa_id') or not self.safa_id:
            while True:
                code = get_random_string(
                    length=5,
                    allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                )
                if not GeographyClub.objects.filter(safa_id=code).exists():
                    # This assumes safa_id field exists in GeographyClub
                    self.safa_id = code
                    break
            self.save(update_fields=['safa_id'])
        return getattr(self, 'safa_id', None)

    def generate_qr_code(self, size=200):
        """Generate QR code for club identification"""
        try:
            from utils.qr_code_utils import generate_qr_code, get_club_qr_data
            qr_data = get_club_qr_data(self)
            return generate_qr_code(qr_data, size)
        except ImportError:
            return None

    @property
    def qr_code(self):
        """Return QR code for club identification"""
        return self.generate_qr_code()

    @classmethod
    def generate_safa_id_for_club(cls, club):
        """Generate a SAFA ID for any club instance"""
        if isinstance(club, GeographyClub):
            if not isinstance(club, cls):
                club = cls.objects.get(pk=club.pk)
            return club.generate_safa_id()
        return None

    @classmethod
    def generate_qr_code_for_club(cls, club, size=200):
        """Generate QR code for any club instance"""
        if isinstance(club, GeographyClub):
            if not isinstance(club, cls):
                club = cls.objects.get(pk=club.pk)
            return club.generate_qr_code(size)
        return None


# ===== SAFA MANAGEMENT UTILITIES =====

class SAFAInvoiceManager:
    """Utility class for managing SAFA invoices and bulk operations"""
    
    @staticmethod
    def create_season_renewal_invoices(season_config):
        """
        Create renewal invoices for all active members for a new season
        Called when is_renewal_season is True
        """
        if not season_config.is_renewal_season:
            raise ValidationError(_("Season is not marked as renewal season"))
        
        created_invoices = []
        
        # Get all active members
        active_members = Member.objects.filter(status='ACTIVE')
        
        for member in active_members:
            try:
                # Check if invoice already exists for this season
                existing = Invoice.objects.filter(
                    season_config=season_config,
                    member=member,
                    invoice_type='RENEWAL'
                ).first()
                
                if not existing:
                    invoice = Invoice.create_safa_registration_invoice(
                        member=member,
                        season_config=season_config
                    )
                    invoice.invoice_type = 'RENEWAL'
                    invoice.save()
                    created_invoices.append(invoice)
                    
            except Exception as e:
                # Log error but continue with other members
                print(f"Error creating renewal invoice for {member}: {e}")
                continue
        
        return created_invoices
    
    @staticmethod
    def calculate_pro_rata_fee(fee_structure, registration_date, season_config):
        """
        Calculate pro-rata fee based on when member registers during season
        """
        if not fee_structure.is_pro_rata:
            return fee_structure.annual_fee
        
        # Calculate months remaining in season
        season_start = season_config.season_start_date
        season_end = season_config.season_end_date
        
        if registration_date <= season_start:
            return fee_structure.annual_fee
        
        if registration_date >= season_end:
            # Use minimum fee if available, otherwise full fee
            return fee_structure.minimum_fee or fee_structure.annual_fee
        
        # Calculate months remaining
        total_season_months = (season_end.year - season_start.year) * 12 + \
                            (season_end.month - season_start.month)
        
        remaining_months = (season_end.year - registration_date.year) * 12 + \
                          (season_end.month - registration_date.month)
        
        if total_season_months <= 0:
            return fee_structure.annual_fee
        
        pro_rata_amount = (fee_structure.annual_fee * remaining_months / total_season_months)
        
        # Apply minimum fee if set
        if fee_structure.minimum_fee:
            pro_rata_amount = max(pro_rata_amount, fee_structure.minimum_fee)
        
        return pro_rata_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def get_overdue_invoices(days_overdue=30):
        """Get all invoices that are overdue by specified days"""
        from datetime import timedelta
        cutoff_date = timezone.now().date() - timedelta(days=days_overdue)
        
        return Invoice.objects.filter(
            status__in=['PENDING', 'PARTIALLY_PAID'],
            due_date__lt=cutoff_date
        )
    
    @staticmethod
    def mark_overdue_invoices():
        """Mark invoices as overdue if past due date"""
        overdue_invoices = Invoice.objects.filter(
            status__in=['PENDING', 'PARTIALLY_PAID'],
            due_date__lt=timezone.now().date()
        )
        
        updated_count = overdue_invoices.update(status='OVERDUE')
        return updated_count


class SAFAReportingUtils:
    """Utility class for SAFA reporting and analytics"""
    
    @staticmethod
    def get_season_revenue_summary(season_config):
        """Get revenue summary for a specific season"""
        invoices = Invoice.objects.filter(season_config=season_config)
        
        return {
            'total_invoiced': invoices.aggregate(
                total=models.Sum('total_amount')
            )['total'] or Decimal('0.00'),
            
            'total_paid': invoices.aggregate(
                total=models.Sum('paid_amount')
            )['total'] or Decimal('0.00'),
            
            'total_outstanding': invoices.aggregate(
                total=models.Sum('outstanding_amount')
            )['total'] or Decimal('0.00'),
            
            'invoice_count': invoices.count(),
            'paid_invoice_count': invoices.filter(status='PAID').count(),
            'overdue_invoice_count': invoices.filter(status='OVERDUE').count(),
            
            'by_type': invoices.values('invoice_type').annotate(
                count=models.Count('id'),
                total_amount=models.Sum('total_amount'),
                paid_amount=models.Sum('paid_amount')
            ),
        }
    
    @staticmethod
    def get_member_registration_stats(season_config=None):
        """Get member registration statistics"""
        if not season_config:
            season_config = SAFASeasonConfig.get_active_season()
        
        if not season_config:
            return {}
        
        members = Member.objects.all()
        
        return {
            'total_members': members.count(),
            'active_members': members.filter(status='ACTIVE').count(),
            'pending_members': members.filter(status='PENDING').count(),
            'junior_members': members.filter(member_type='JUNIOR').count(),
            'senior_members': members.filter(member_type='SENIOR').count(),
            'officials': members.filter(member_type='OFFICIAL').count(),
            
            'by_province': members.values(
                'province__name'
            ).annotate(
                count=models.Count('id')
            ).order_by('-count'),
            
            'by_club': members.values(
                'club__name'
            ).annotate(
                count=models.Count('id')
            ).order_by('-count')[:10],  # Top 10 clubs
        }


# ===== SIGNALS AND POST-SAVE HOOKS =====

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=InvoiceItem)
def update_invoice_totals_on_item_save(sender, instance, **kwargs):
    """Recalculate invoice totals when line items change"""
    if instance.invoice_id:
       instance.invoice.recalculate_totals()

@receiver(post_delete, sender=InvoiceItem)
def update_invoice_totals_on_item_delete(sender, instance, **kwargs):
    """Recalculate invoice totals when line items are deleted"""
    if instance.invoice_id:
        instance.invoice.recalculate_totals()

@receiver(post_save, sender=Member)
def create_safa_registration_invoice(sender, instance, created, **kwargs):
    """Auto-create SAFA registration invoice for new members"""
    if created and instance.status == 'PENDING':
        try:
            active_season = SAFASeasonConfig.get_active_season()
            if active_season:
                # Check if invoice already exists
                existing_invoice = Invoice.objects.filter(
                    member=instance,
                    season_config=active_season,
                    invoice_type='REGISTRATION'
                ).first()
                if not existing_invoice:
                    Invoice.create_safa_registration_invoice(
                        member=instance,
                        season_config=active_season
                    )
        except Exception as e:
            # Log error but don't prevent member creation
            print(f"Error creating SAFA registration invoice for {instance}: {e}")


@receiver(post_save, sender=SAFASeasonConfig)
def handle_new_season_activation(sender, instance, **kwargs):
    """Handle activation of new SAFA season"""
    if instance.is_active and instance.is_renewal_season:
        try:
            # Create renewal invoices for all active members
            SAFAInvoiceManager.create_season_renewal_invoices(instance)
        except Exception as e:
            print(f"Error creating season renewal invoices: {e}")


# ===== ADMIN INTEGRATION HELPERS =====

class SAFAAdminMixin:
    """Mixin for Django admin to add SAFA-specific functionality"""

    def get_safa_status(self, obj):
        """Get SAFA registration status for members"""
        if hasattr(obj, 'status'):
            return obj.get_status_display()
        return "N/A"
    get_safa_status.short_description = "SAFA Status"

    def has_paid_invoices(self, obj):
        """Check if member has paid invoices"""
        if hasattr(obj, 'invoices'):
            return obj.invoices.filter(status='PAID').exists()
        return False
    has_paid_invoices.boolean = True
    has_paid_invoices.short_description = "Has Paid"

    def get_outstanding_amount(self, obj):
        """Get total outstanding amount for member"""
        if hasattr(obj, 'invoices'):
            total = obj.invoices.aggregate(
                total=models.Sum('outstanding_amount')
            )['total']
            return f"R{total or 0:.2f}"
        return "R0.00"
    get_outstanding_amount.short_description = "Outstanding"


# ===== CUSTOM EXCEPTIONS =====

class SAFARegistrationError(Exception):
    """Custom exception for SAFA registration errors"""
    pass


class SAFAInvoiceError(Exception):
    """Custom exception for SAFA invoice errors"""
    pass


class SAFASeasonConfigError(Exception):
    """Custom exception for SAFA season configuration errors"""
    pass


# ===== MODEL VALIDATION UTILITIES =====

def validate_safa_id_format(value):
    """Validate SAFA ID format"""
    if value and (len(value) != 5 or not value.isalnum() or not value.isupper()):
        raise ValidationError(_("SAFA ID must be 5 uppercase alphanumeric characters"))


def validate_fifa_id_format(value):
    """Validate FIFA ID format"""
    if value and (len(value) != 7 or not value.isdigit()):
        raise ValidationError(_("FIFA ID must be 7 digits"))


def validate_sa_id_number(value):
    """Validate South African ID number"""
    if value:
        if not value.isdigit() or len(value) != 13:
            raise ValidationError(_("SA ID number must be 13 digits"))

# Additional Luhn algorithm validation could be added here
# This is implemented in the Member model's _validate_id_number method

