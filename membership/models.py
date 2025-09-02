# membership/models.py - CORRECTED and Complete Implementation

from django.db import models, transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import RegexValidator
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from model_utils.models import TimeStampedModel
from decimal import Decimal, ROUND_HALF_UP
import uuid
from datetime import date, timedelta
from .safa_config_models import SAFASeasonConfig, SAFAFeeStructure

# Constants
MEMBER_ROLES = [
    ('PLAYER', _('Player')),
    ('OFFICIAL', _('Official')),
    ('ADMIN', _('Administrator')),
    ('SUPPORTER', _('Supporter')),
]

MEMBERSHIP_STATUS = [
    ('PENDING', _('Pending SAFA Approval')),
    ('ACTIVE', _('SAFA Approved - Active')),
    ('INACTIVE', _('Inactive')),
    ('SUSPENDED', _('Suspended')),
    ('REJECTED', _('Rejected by SAFA')),
    ('TRANSFERRED', _('Transferred from another club')),
]

# GIS imports
# try:
#     from django.contrib.gis.db import models as gis_models
#     from django.contrib.gis.geos import Point
#     GIS_AVAILABLE = True
# except ImportError:
gis_models = models
Point = None
GIS_AVAILABLE = False

# try:
#     import geocoder
#     GEOCODER_AVAILABLE = True
# except ImportError:
GEOCODER_AVAILABLE = False

# Models






class Member(TimeStampedModel):
    """
    Centralized Member model - handles all member types
    """
    # Class-level constants
    REGISTRATION_METHODS = [
        ('SELF', _('Self Registration Online')),
        ('CLUB', _('Club Registration')),
        ('ADMIN', _('Admin Registration')),
    ]

    safa_id = models.CharField(
        _("SAFA ID"),
        max_length=5,
        unique=True,
        help_text=_("5-digit unique SAFA identification number"),
        default=''
    )

    # Track if this is existing member or new registration
    is_existing_member = models.BooleanField(
        _("Existing SAFA Member"),
        default=False,
        help_text=_("Whether this member already had a SAFA ID from previous registration")
    )
    previous_safa_id = models.CharField(
        _("Previous SAFA ID"),
        max_length=5,
        blank=True, null=True,
        help_text=_("Previous SAFA ID if this is a transfer/renewal")
    )

    # Personal Information
    first_name = models.CharField(_("First Name"), max_length=100, null=True, blank=True)
    last_name = models.CharField(_("Last Name"), max_length=100, null=True, blank=True)
    email = models.EmailField(_("Email Address"), null=True, blank=True)
    phone_number = models.CharField(
        _("Phone Number"),
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\s\-\(\)]{10,20}$',
                message=_('Enter a valid phone number')
            )
        ]
    )
    date_of_birth = models.DateField(_("Date of Birth"), null=True, blank=True)
    gender = models.CharField(_("Gender"), max_length=1, choices=[('M', 'Male'), ('F', 'Female')], blank=True, null=True)

    # ID Information
    id_number = models.CharField(
        _("ID Number"),
        max_length=13,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\d{13}$',
                message=_('ID number must be exactly 13 digits')
            )
        ]
    )
    passport_number = models.CharField(_('Passport Number'), max_length=25, blank=True, null=True)

    # Address Information
    street_address = models.CharField(_("Street Address"), max_length=255, blank=True, null=True)
    suburb = models.CharField(_("Suburb"), max_length=100, blank=True, null=True)
    city = models.CharField(_("City"), max_length=100, blank=True, null=True)
    state = models.CharField(_("State/Province"), max_length=100, blank=True, null=True)
    postal_code = models.CharField(_("Postal Code"), max_length=20, blank=True, null=True)
    country = models.CharField(_("Country"), max_length=100, blank=True, null=True)

    # SAFA Registration Details
    role = models.CharField(_("Member Role"), max_length=20, choices=MEMBER_ROLES, null=True, blank=True)
    status = models.CharField(_("SAFA Status"), max_length=20, choices=MEMBERSHIP_STATUS, default='PENDING')
    nationality = models.CharField(
        _("Nationality"),
        max_length=100, blank=True,
        default="South African"
    )
    registration_complete = models.BooleanField(
        _("Registration Complete"),
        default=False,
        help_text=_("All required documents and information provided")
    )

    # Card Preferences
    physical_card_requested = models.BooleanField(
        _("Physical Card Requested"),
        default=False,
        help_text=_("Whether the member has requested a physical membership card.")
    )
    CARD_DELIVERY_CHOICES = [
        ('DIGITAL_ONLY', _('Digital Only')),
        ('PHYSICAL_ONLY', _('Physical Only')),
        ('BOTH', _('Both Digital and Physical')),
    ]
    card_delivery_preference = models.CharField(
        _("Card Delivery Preference"),
        max_length=20,
        choices=CARD_DELIVERY_CHOICES,
        default='DIGITAL_ONLY',
        help_text=_("Preferred method for receiving membership cards.")
    )
    physical_card_delivery_address = models.TextField(
        _("Physical Card Delivery Address"),
        blank=True,
        help_text=_("Address for physical card delivery, if different from primary address.")
    )

    # Registration method and current season
    registration_method = models.CharField(
        _("Registration Method"),
        max_length=10,
        choices=REGISTRATION_METHODS,
        default='SELF'
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='member_profile',
        verbose_name=_("Associated User Account")
    )
    current_season = models.ForeignKey(
        SAFASeasonConfig,
        on_delete=models.PROTECT,
        related_name='current_season_members',
        help_text=_("Season this member is registered for"),
        null=True, blank=True
    )

    # CORRECTED: Single club membership (mandatory during registration)
    current_club = models.ForeignKey(
        'geography.Club',  # String reference to avoid circular imports
        on_delete=models.SET_NULL,
        null=True, blank=True,  # Club selection is NOT mandatory
        related_name='current_members',
        help_text=_("Current club this member belongs to")
    )

    # Approval tracking
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_members'
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True)

    # Geographic/Organizational Hierarchy (auto-detected or selected)
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
    national_federation = models.ForeignKey(
        'geography.NationalFederation',
        on_delete=models.PROTECT,
        default=1
    )

    # CORRECTED: Multiple associations for officials (referee, coaching, etc.)
    associations = models.ManyToManyField(
        'geography.Association',
        blank=True,
        related_name='member_officials',
        help_text=_("Associations this member belongs to (referee, coaching, etc.)")
    )

    # Location-based organization detection (for self-registration)
    registration_address = models.CharField(
        _("Registration Address"),
        max_length=255,
        blank=True,
        help_text=_("Address used to determine organization jurisdiction")
    )

    # Geographic coordinates for automatic organization assignment
    location = gis_models.PointField(
        _("Geographic Location"),
        null=True, blank=True,
        help_text=_("GPS coordinates for organization assignment")
    ) if GIS_AVAILABLE else models.CharField(
        _("Location Placeholder"),
        max_length=100,
        blank=True,
        help_text=_("Install PostGIS for full geographic support")
    )

    # Self-registration validation
    terms_accepted = models.BooleanField(_("Terms and Conditions Accepted"), default=False)
    privacy_accepted = models.BooleanField(_("Privacy Policy Accepted"), default=False)
    marketing_consent = models.BooleanField(_("Marketing Consent"), default=False)

    # Documents and Images
    profile_picture = models.ImageField(
        _("Profile Picture"),
        upload_to='member_profiles/',
        null=True, blank=True
    )
    id_document = models.FileField(
        upload_to='documents/member_documents/',
        null=True, blank=True
    )

    # Emergency Contact
    emergency_contact = models.CharField(_("Emergency Contact"), max_length=100, blank=True)
    emergency_phone = models.CharField(_("Emergency Contact Phone"), max_length=20, blank=True)
    medical_notes = models.TextField(_("Medical Notes"), blank=True)

    class Meta:
        verbose_name = _("Member")
        verbose_name_plural = _("Members")
        ordering = ['-created']
        indexes = [
            models.Index(fields=['safa_id']),
            models.Index(fields=['email']),
            models.Index(fields=['current_club', 'status']),
            models.Index(fields=['current_season', 'status']),
            models.Index(fields=['role', 'status']),
        ]

    def __str__(self):
        club_name = self.current_club.name if self.current_club else "No Club"
        return f"{self.first_name} {self.last_name} ({self.safa_id}) - {club_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_junior(self):
        """Check if member is under 18"""
        if self.date_of_birth:
            age = (timezone.now().date() - self.date_of_birth).days // 365
            return age < 18
        return False

    @property
    def age(self):
        """Calculate member's age"""
        if self.date_of_birth:
            return (timezone.now().date() - self.date_of_birth).days // 365
        return None

    def clean(self):
        super().clean()

        # CORRECTED: Club selection is mandatory
        if not self.current_club:
            raise ValidationError(_("Club selection is mandatory during registration"))

        # Validate club is within member's geographic area
        self.validate_club_geography()

        # Validate SA ID number if provided
        if self.id_number:
            self.validate_sa_id_number()

        # Check if member can register based on organization payment status
        if not self.pk:  # New member
            if not self.can_register_with_organization():
                raise ValidationError(_(
                    "Cannot register member. The organization must be paid up for the current season first."
                ))

    def save(self, *args, **kwargs):
        # Set current season if not set
        if not self.current_season_id:
            self.current_season = SAFASeasonConfig.get_active_season()

        # Handle SAFA ID - only generate if none provided
        if not self.safa_id:
            self.generate_safa_id()
        elif self.is_existing_member and not self.previous_safa_id:
            self.validate_existing_safa_id()

        # Auto-detect organization if doing self-registration
        if self.registration_method == 'SELF' and self.registration_address and GIS_AVAILABLE:
            if not self.location:
                self.geocode_address()

            if self.location and not (self.province or self.region or self.lfa):
                self.assign_organization_by_location()

        super().save(*args, **kwargs)

    def geocode_address(self):
        """Convert address to GPS coordinates"""
        if not GEOCODER_AVAILABLE or not GIS_AVAILABLE:
            return

        try:
            g = geocoder.google(self.registration_address)
            if g.ok:
                self.location = Point(g.lng, g.lat)
        except Exception as e:
            print(f"Geocoding failed for {self.registration_address}: {e}")

    def assign_organization_by_location(self):
        """Assign organization based on geographic location"""
        if not self.location or not GIS_AVAILABLE:
            return

        try:
            # Import here to avoid circular imports
            from geography.models import LocalFootballAssociation, Region, Province

            # Check for LFA (most specific)
            lfa = LocalFootballAssociation.objects.filter(
                boundary__contains=self.location,
                is_active=True
            ).first()

            if lfa:
                self.lfa = lfa
                self.region = lfa.region
                self.province = lfa.region.province if lfa.region else None
                return

            # Check for Region
            region = Region.objects.filter(
                boundary__contains=self.location,
                is_active=True
            ).first()

            if region:
                self.region = region
                self.province = region.province
                return

            # Check for Province
            province = Province.objects.filter(
                boundary__contains=self.location,
                is_active=True
            ).first()

            if province:
                self.province = province

        except Exception as e:
            print(f"Organization assignment failed: {e}")

    def generate_safa_id(self):
        """Generate a unique 5-character SAFA ID"""
        while True:
            code = get_random_string(
                length=5,
                allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            )
            if not Member.objects.filter(safa_id=code).exists():
                self.safa_id = code
                break

    def validate_existing_safa_id(self):
        """Validate that the provided SAFA ID exists in previous seasons"""
        if not self.safa_id or len(self.safa_id) != 5:
            raise ValidationError(_("Invalid existing SAFA ID format"))

    def can_register_with_organization(self):
        """Check if member can register based on organization payment status"""
        if not self.current_season:
            return False

        # Get the organization this member belongs to
        organization = self.get_primary_organization()
        if not organization:
            return True  # If no organization specified, allow registration

        # Check if organization is paid up for the season
        content_type = ContentType.objects.get_for_model(organization)
        try:
            org_registration = OrganizationSeasonRegistration.objects.get(
                season_config=self.current_season,
                content_type=content_type,
                object_id=organization.pk
            )
            return org_registration.can_register_members()
        except OrganizationSeasonRegistration.DoesNotExist:
            return False

    def get_primary_organization(self):
        """Get the primary organization this member belongs to"""
        # Priority: LFA > Region > Province
        if self.lfa:
            return self.lfa
        elif self.region:
            return self.region
        elif self.province:
            return self.province
        return None

    def approve_safa_membership(self, approved_by):
        """Approve the member's SAFA registration"""
        self.status = 'ACTIVE'
        self.approved_by = approved_by
        self.approved_date = timezone.now()
        self.save()

    def reject_safa_membership(self, rejected_by, reason):
        """Reject the member's SAFA registration"""
        self.status = 'REJECTED'
        self.rejection_reason = reason
        self.save()

    def get_entity_type_for_fees(self):
        """Get the entity type for fee calculation"""
        if self.role == 'PLAYER':
            return 'PLAYER_JUNIOR' if self.is_junior else 'PLAYER_SENIOR'
        elif self.role == 'OFFICIAL':
            # Try to get specific official type from MemberProfile
            try:
                profile = self.profile
                if profile.official_position:
                    position_title = profile.official_position.title.lower()
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
            except (AttributeError, ObjectDoesNotExist):
                # Handle cases where profile or official_position doesn't exist
                pass
            return 'OFFICIAL_GENERAL'
        return 'PLAYER_SENIOR'  # Default fallback

    def validate_club_geography(self):
        """Ensure selected club is within member's geographic area"""
        if not self.current_club:
            return

        club = self.current_club

        # Check if club is in member's LFA/Region/Province
        club = self.current_club

        # Check if club is in member's LFA/Region/Province
        if self.lfa and club.localfootballassociation != self.lfa: # Line 510
            raise ValidationError(_(
                f"Selected club {club.name} is not in your Local Football Association area"
            ))
        elif self.region and club.region != self.region:
            raise ValidationError(_(
                f"Selected club {club.name} is not in your Regional area"
            ))
        elif self.province and club.province != self.province:
            raise ValidationError(_(
                f"Selected club {club.name} is not in your Provincial area"
            ))

    def validate_sa_id_number(self):
        """Validate South African ID number and extract birth date"""
        if not self.id_number or len(self.id_number) != 13:
            return

        try:
            # Extract birth date from ID (YYMMDD format)
            year = int(self.id_number[:2])
            month = int(self.id_number[2:4])
            day = int(self.id_number[4:6])

            # Determine century (assume < 25 = 2000s, >= 25 = 1900s)
            if year < 25:
                year += 2000
            else:
                year += 1900

            id_birth_date = date(year, month, day)

            # If no birth date set, use ID date
            if not self.date_of_birth:
                self.date_of_birth = id_birth_date
            # If birth date differs from ID, flag for review
            elif self.date_of_birth != id_birth_date:
                raise ValidationError(_(
                    "Birth date doesn't match ID number. Please verify your information."
                ))

            # Extract gender from ID (7th digit: 0-4=Female, 5-9=Male)
            gender_digit = int(self.id_number[6])
            id_gender = 'M' if gender_digit >= 5 else 'F'

            if not self.gender:
                self.gender = id_gender
            elif self.gender != id_gender:
                raise ValidationError(_(
                    "Gender doesn't match ID number. Please verify your information."
                ))

        except (ValueError, IndexError):
            raise ValidationError(_("Invalid South African ID number format"))

    def get_available_clubs(self):
        """Get clubs available for this member based on geography"""
        from geography.models import Club

        if self.lfa:
            return Club.objects.filter(lfa=self.lfa, is_active=True)
        elif self.region:
            return Club.objects.filter(region=self.region, is_active=True)
        elif self.province:
            return Club.objects.filter(province=self.province, is_active=True)
        else:
            # If no geography set, return all active clubs
            return Club.objects.filter(is_active=True)

    def calculate_registration_fee(self, season_config=None):
        """Calculate member's registration fee including pro-rata if applicable"""
        import logging
        logger = logging.getLogger(__name__)

        if not season_config:
            season_config = self.current_season or SAFASeasonConfig.get_active_season()
        
        if not season_config:
            logger.warning("No active season found for fee calculation.")
            return Decimal('0.00')

        entity_type = self.get_entity_type_for_fees()
        logger.info(f"Calculating fee for member {self.safa_id}, entity_type: {entity_type}, season: {season_config.season_year}")

        fee_structure = SAFAFeeStructure.objects.filter(
            season_config=season_config,
            entity_type=entity_type
        ).first()

        if not fee_structure:
            logger.warning(f"No SAFAFeeStructure found for entity_type: {entity_type} and season: {season_config.season_year}")
            # Return a default fee if no fee structure is found
            if entity_type == 'PLAYER_JUNIOR':
                return Decimal('100.00')
            elif entity_type == 'PLAYER_SENIOR':
                return Decimal('200.00')
            elif 'OFFICIAL' in entity_type:
                return Decimal('250.00')
            else:
                return Decimal('200.00')  # Default fee

        base_fee = fee_structure.annual_fee
        logger.info(f"Base fee for {entity_type}: {base_fee}")

        # Apply pro-rata if applicable and registration is after season start
        if fee_structure.is_pro_rata and season_config:
            today = timezone.now().date()
            if today > season_config.season_start_date:
                # Calculate months remaining
                season_days = (season_config.season_end_date - season_config.season_start_date).days
                remaining_days = (season_config.season_end_date - today).days

                if remaining_days > 0:
                    pro_rata_fee = base_fee * (Decimal(remaining_days) / Decimal(season_days))
                    # Apply minimum fee if set
                    if fee_structure.minimum_fee:
                        pro_rata_fee = max(pro_rata_fee, fee_structure.minimum_fee)
                    logger.info(f"Applied pro-rata fee: {pro_rata_fee}")
                    return pro_rata_fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                else:
                    logger.info("No remaining days for pro-rata calculation, returning base fee.")

        return base_fee

    def calculate_simple_registration_fee(self, season_config=None):
        """Calculate member's registration fee using the specific formula: Fee = Total / 1.15, VAT = Fee * 15%"""
        import logging
        logger = logging.getLogger(__name__)

        if not season_config:
            season_config = self.current_season or SAFASeasonConfig.get_active_season()
        
        if not season_config:
            logger.warning("No active season found for fee calculation.")
            return Decimal('0.00')

        entity_type = self.get_entity_type_for_fees()
        logger.info(f"Calculating simple fee for member {self.safa_id}, entity_type: {entity_type}, season: {season_config.season_year}")

        fee_structure = SAFAFeeStructure.objects.filter(
            season_config=season_config,
            entity_type=entity_type
        ).first()

        if not fee_structure:
            logger.warning(f"No SAFAFeeStructure found for entity_type: {entity_type} and season: {season_config.season_year}")
            # Return a default fee if no fee structure is found
            if entity_type == 'PLAYER_JUNIOR':
                total_amount = Decimal('100.00')
            elif entity_type == 'PLAYER_SENIOR':
                total_amount = Decimal('200.00')
            elif 'OFFICIAL' in entity_type:
                total_amount = Decimal('250.00')
            else:
                total_amount = Decimal('200.00')  # Default fee
        else:
            total_amount = fee_structure.annual_fee

        # Use the specific formula: Fee = Total / 1.15
        fee_excluding_vat = total_amount / Decimal('1.15')  # R200 / 1.15 = R173.91
        
        logger.info(f"Simple fee calculation: Total={total_amount}, Fee (excl. VAT)={fee_excluding_vat}")
        
        return fee_excluding_vat


class Transfer(TimeStampedModel):
    """
    Member transfers between clubs (single club membership)
    """
    STATUS_CHOICES = [
        ('PENDING', _('Pending Approval')),
        ('APPROVED', _('Approved')),
        ('REJECTED', _('Rejected')),
        ('CANCELLED', _('Cancelled')),
    ]

    member = models.ForeignKey(
        'membership.Member',  # Use consistent string reference
        on_delete=models.CASCADE,
        related_name='transfers'
    )
    from_club = models.ForeignKey(
        'geography.Club',
        on_delete=models.CASCADE,
        related_name='transfers_out'
    )
    to_club = models.ForeignKey(
        'geography.Club',
        on_delete=models.CASCADE,
        related_name='transfers_in'
    )
    request_date = models.DateField(_("Request Date"), default=timezone.now)
    effective_date = models.DateField(_("Effective Date"), null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    reason = models.TextField(_("Transfer Reason"), blank=True)
    transfer_fee = models.DecimalField(
        _("Transfer Fee"),
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # Approval details
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_transfers'
    )
    approved_date = models.DateTimeField(_("Approval Date"), null=True, blank=True)
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True)

    class Meta:
        verbose_name = _("Transfer")
        verbose_name_plural = _("Transfers")
        ordering = ['-request_date']
        indexes = [
            models.Index(fields=['member', 'status']),
            models.Index(fields=['from_club', 'status']),
            models.Index(fields=['to_club', 'status']),
            models.Index(fields=['request_date']),
        ]

    def __str__(self):
        return f"{self.member.get_full_name()} - {self.from_club.name} to {self.to_club.name}"

    def clean(self):
        super().clean()
        if self.from_club == self.to_club:
            raise ValidationError(_("Cannot transfer member to the same club"))

        # Check member's current club matches from_club
        if self.member.current_club != self.from_club:
            raise ValidationError(_("Member's current club must match the transfer source club"))

    def approve(self, approved_by):
        """Approve the transfer and update member's current club"""
        if self.status != 'PENDING':
            raise ValidationError(_("Only pending transfers can be approved"))

        with transaction.atomic():
            # Update member's current club
            old_club = self.member.current_club
            self.member.current_club = self.to_club
            self.member.save()

            # Update transfer record
            self.status = 'APPROVED'
            self.approved_by = approved_by
            self.approved_date = timezone.now()
            self.effective_date = timezone.now().date()
            self.save()

            # Update season history if exists
            try:
                history = MemberSeasonHistory.objects.get(
                    member=self.member,
                    season_config=self.member.current_season
                )
                history.transferred_from_club = old_club
                history.club = self.to_club
                history.transfer_date = self.effective_date
                history.save()
            except MemberSeasonHistory.DoesNotExist:
                pass

    def reject(self, rejected_by, reason):
        """Reject the transfer"""
        if self.status != 'PENDING':
            raise ValidationError(_("Only pending transfers can be rejected"))

        self.status = 'REJECTED'
        self.approved_by = rejected_by
        self.approved_date = timezone.now()
        self.rejection_reason = reason
        self.save()


# ============================================================================
# LEGACY MODEL SUPPORT (For backward compatibility)
# ============================================================================

# Keep existing models for backward compatibility but mark as deprecated
class Membership(TimeStampedModel):
    """
    DEPRECATED: Use Member model instead
    Kept for backward compatibility only
    """
    member = models.OneToOneField(
        'membership.Member',  # Use consistent string reference
        on_delete=models.CASCADE,
        related_name='legacy_membership'
    )
    membership_type = models.CharField(max_length=20, default='STANDARD')

    class Meta:
        verbose_name = _("Legacy Membership")
        verbose_name_plural = _("Legacy Memberships")

    def __str__(self):
        return f"Legacy: {self.member.get_full_name()}"


# ============================================================================
# DJANGO SIGNALS FOR DATA CONSISTENCY
# ============================================================================

@receiver(post_save, sender='membership.Member')
def create_member_workflow(sender, instance, created, **kwargs):
    """Create workflow tracker for new members"""
    if created:
        RegistrationWorkflow.objects.get_or_create(member=instance)

@receiver(post_save, sender='membership.Member')
def update_club_quotas(sender, instance, **kwargs):
    """Update club member quotas when member is saved"""
    if instance.current_club and instance.current_season:
        quota, created = ClubMemberQuota.objects.get_or_create(
            club=instance.current_club,
            season_config=instance.current_season
        )
        quota.update_counts()

@receiver(post_delete, sender='membership.Member')
def update_club_quotas_on_delete(sender, instance, **kwargs):
    """Update club quotas when member is deleted"""
    if instance.current_club and instance.current_season:
        try:
            quota = ClubMemberQuota.objects.get(
                club=instance.current_club,
                season_config=instance.current_season
            )
            quota.update_counts()
        except ClubMemberQuota.DoesNotExist:
            pass

@receiver(post_save, sender=SAFASeasonConfig)
def handle_season_activation(sender, instance, **kwargs):
    """Handle season activation - deactivate other seasons"""
    if instance.is_active:
        # Deactivate all other seasons
        SAFASeasonConfig.objects.exclude(pk=instance.pk).update(is_active=False)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_current_season():
    """Utility function to get current active season"""
    return SAFASeasonConfig.get_active_season()

def calculate_member_fee(member, season_config=None):
    """Utility function to calculate member registration fee"""
    if not season_config:
        season_config = get_current_season()

    if not season_config or not member:
        return Decimal('0.00')

    return member.calculate_registration_fee(season_config)

def check_organization_payment_status(organization, season_config=None):
    """Check if organization has paid for the season"""
    if not season_config:
        season_config = get_current_season()

    if not season_config or not organization:
        return False

    content_type = ContentType.objects.get_for_model(organization)
    try:
        registration = OrganizationSeasonRegistration.objects.get(
            season_config=season_config,
            content_type=content_type,
            object_id=organization.pk
        )
        return registration.can_register_members()
    except OrganizationSeasonRegistration.DoesNotExist:
        return False


class OrganizationSeasonRegistration(TimeStampedModel):
    """
    Tracks organization registrations and payments for each season
    Organizations must pay first before their members can register
    """
    REGISTRATION_STATUS = [
        ('PENDING', _('Pending Payment')),
        ('PAID', _('Paid - Active')),
        ('OVERDUE', _('Overdue')),
        ('SUSPENDED', _('Suspended')),
    ]

    season_config = models.ForeignKey(
        SAFASeasonConfig,
        on_delete=models.CASCADE,
        related_name='organization_registrations'
    )

    # Generic foreign key to handle different organization types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    organization = GenericForeignKey('content_type', 'object_id')

    # Registration details
    registration_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=REGISTRATION_STATUS, default='PENDING')

    # Payment tracking
    invoice = models.OneToOneField(
        'Invoice',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='organization_registration'
    )

    # Administrative
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='registered_organizations'
    )

    class Meta:
        verbose_name = _("Organization Season Registration")
        verbose_name_plural = _("Organization Season Registrations")
        unique_together = [('season_config', 'content_type', 'object_id')]
        indexes = [
            models.Index(fields=['season_config', 'status']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        org_name = getattr(self.organization, 'name', str(self.organization))
        return f"{org_name} - Season {self.season_config.season_year} ({self.status})"

    @property
    def organization_name(self):
        """Get organization name regardless of type"""
        return getattr(self.organization, 'name', str(self.organization))

    @property
    def organization_type(self):
        """Get organization type"""
        return self.content_type.model.upper()

    def can_register_members(self):
        """Check if organization can register members (payment confirmed)"""
        return self.status == 'PAID'


class ClubMemberQuota(models.Model):
    """Track member quotas and limits per club per season"""
    club = models.ForeignKey(
        'geography.Club',
        on_delete=models.CASCADE,
        related_name='member_quotas'
    )
    season_config = models.ForeignKey(
        SAFASeasonConfig,
        on_delete=models.CASCADE,
        related_name='club_quotas'
    )

    # Quota limits
    max_senior_players = models.PositiveIntegerField(
        _("Max Senior Players"),
        default=30,
        help_text=_("Maximum senior players allowed")
    )
    max_junior_players = models.PositiveIntegerField(
        _("Max Junior Players"),
        default=50,
        help_text=_("Maximum junior players allowed")
    )
    max_officials = models.PositiveIntegerField(
        _("Max Officials"),
        default=20,
        help_text=_("Maximum officials allowed")
    )

    # Current counts (updated via signals)
    current_senior_players = models.PositiveIntegerField(default=0)
    current_junior_players = models.PositiveIntegerField(default=0)
    current_officials = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [('club', 'season_config')]
        verbose_name = _("Club Member Quota")
        verbose_name_plural = _("Club Member Quotas")

    def __str__(self):
        return f"{self.club.name} - Season {self.season_config.season_year} Quotas"

    def can_register_member(self, member_type):
        """Check if club can register another member of given type"""
        if member_type == 'senior_player':
            return self.current_senior_players < self.max_senior_players
        elif member_type == 'junior_player':
            return self.current_junior_players < self.max_junior_players
        elif member_type == 'official':
            return self.current_officials < self.max_officials
        return False

    def update_counts(self):
        """Update current member counts"""
        # Get current season members for this club
        members = Member.objects.filter(
            current_club=self.club,
            current_season=self.season_config,
            status='ACTIVE'
        )

        self.current_senior_players = members.filter(
            role='PLAYER',
            date_of_birth__lt=timezone.now().date().replace(
                year=timezone.now().year - 18
            )
        ).count()

        self.current_junior_players = members.filter(
            role='PLAYER',
            date_of_birth__gte=timezone.now().date().replace(
                year=timezone.now().year - 18
            )
        ).count()

        self.current_officials = members.filter(
            role='OFFICIAL'
        ).count()

        self.save()


class MemberDocument(TimeStampedModel):
    """Enhanced document management for members"""
    DOCUMENT_TYPES = [
        ('ID_COPY', _('ID Document Copy')),
        ('BIRTH_CERT', _('Birth Certificate')),
        ('PASSPORT', _('Passport Copy')),
        ('MEDICAL_CERT', _('Medical Certificate')),
        ('CLEARANCE_CERT', _('Clearance Certificate')),
        ('PHOTO', _('Passport Photo')),
        ('PARENT_CONSENT', _('Parental Consent (Under 18)')),
        ('PROOF_RESIDENCE', _('Proof of Residence')),
        ('QUALIFICATION_CERT', _('Qualification Certificate')),
        ('OTHER', _('Other Document')),
    ]

    VERIFICATION_STATUS = [
        ('PENDING', _('Pending Verification')),
        ('APPROVED', _('Approved')),
        ('REJECTED', _('Rejected - Resubmission Required')),
    ]

    member = models.ForeignKey(
        'membership.Member',  # Use consistent string reference
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(
        _("Document Type"),
        max_length=20,
        choices=DOCUMENT_TYPES
    )
    document_file = models.FileField(
        _("Document File"),
        upload_to='member_documents/%Y/%m/'
    )
    verification_status = models.CharField(
        _("Verification Status"),
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='PENDING'
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_documents'
    )
    verified_date = models.DateTimeField(null=True, blank=True)
    rejection_notes = models.TextField(_("Rejection Notes"), blank=True)

    # Document metadata
    file_size = models.PositiveIntegerField(_("File Size (bytes)"), null=True, blank=True)
    file_type = models.CharField(_("File Type"), max_length=50, blank=True)
    is_required = models.BooleanField(_("Required Document"), default=False)
    expiry_date = models.DateField(_("Document Expiry"), null=True, blank=True)

    class Meta:
        unique_together = [('member', 'document_type')]
        verbose_name = _("Member Document")
        verbose_name_plural = _("Member Documents")
        indexes = [
            models.Index(fields=['member', 'document_type']),
            models.Index(fields=['verification_status']),
        ]

    def __str__(self):
        return f"{self.member.get_full_name()} - {self.get_document_type_display()}"

    def save(self, *args, **kwargs):
        if self.document_file:
            self.file_size = self.document_file.size
            self.file_type = self.document_file.name.split('.')[-1].upper()
        super().save(*args, **kwargs)

    def approve(self, verified_by):
        """Approve the document"""
        self.verification_status = 'APPROVED'
        self.verified_by = verified_by
        self.verified_date = timezone.now()
        self.rejection_notes = ''
        self.save()

    def reject(self, verified_by, notes):
        """Reject the document with notes"""
        self.verification_status = 'REJECTED'
        self.verified_by = verified_by
        self.verified_date = timezone.now()
        self.rejection_notes = notes
        self.save()


class RegistrationWorkflow(TimeStampedModel):
    """Track member registration progress through required steps"""
    WORKFLOW_STEPS = [
        ('PERSONAL_INFO', _('Personal Information')),
        ('CLUB_SELECTION', _('Club Selection')),
        ('DOCUMENT_UPLOAD', _('Document Upload')),
        ('PAYMENT', _('Payment Processing')),
        ('CLUB_APPROVAL', _('Club Approval')),
        ('SAFA_APPROVAL', _('SAFA Approval')),
        ('COMPLETE', _('Registration Complete')),
    ]

    STEP_STATUS = [
        ('NOT_STARTED', _('Not Started')),
        ('IN_PROGRESS', _('In Progress')),
        ('COMPLETED', _('Completed')),
        ('BLOCKED', _('Blocked')),
    ]

    member = models.OneToOneField(
        'membership.Member',  # Use consistent string reference
        on_delete=models.CASCADE,
        related_name='workflow'
    )

    # Step statuses
    personal_info_status = models.CharField(
        max_length=20, choices=STEP_STATUS, default='NOT_STARTED'
    )
    club_selection_status = models.CharField(
        max_length=20, choices=STEP_STATUS, default='NOT_STARTED'
    )
    document_upload_status = models.CharField(
        max_length=20, choices=STEP_STATUS, default='NOT_STARTED'
    )
    payment_status = models.CharField(
        max_length=20, choices=STEP_STATUS, default='NOT_STARTED'
    )
    club_approval_status = models.CharField(
        max_length=20, choices=STEP_STATUS, default='NOT_STARTED'
    )
    safa_approval_status = models.CharField(
        max_length=20, choices=STEP_STATUS, default='NOT_STARTED'
    )

    current_step = models.CharField(
        _("Current Step"),
        max_length=20,
        choices=WORKFLOW_STEPS,
        default='PERSONAL_INFO'
    )

    completion_percentage = models.PositiveIntegerField(
        _("Completion %"),
        default=0
    )

    class Meta:
        verbose_name = _("Registration Workflow")
        verbose_name_plural = _("Registration Workflows")

    def __str__(self):
        return f"{self.member.get_full_name()} - {self.completion_percentage}% Complete"

    def update_progress(self):
        """Update workflow progress based on completed steps"""
        steps = [
            self.personal_info_status,
            self.document_upload_status,
            self.payment_status,
            self.safa_approval_status,
        ]

        if self.member.role != 'SUPPORTER':
            steps.extend([
                self.club_selection_status,
                self.club_approval_status,
            ])

        completed_steps = sum(1 for status in steps if status == 'COMPLETED')
        self.completion_percentage = int((completed_steps / len(steps)) * 100) if len(steps) > 0 else 0

        # Update current step
        if self.personal_info_status != 'COMPLETED':
            self.current_step = 'PERSONAL_INFO'
        elif self.member.role != 'SUPPORTER' and self.club_selection_status != 'COMPLETED':
            self.current_step = 'CLUB_SELECTION'
        elif self.document_upload_status != 'COMPLETED':
            self.current_step = 'DOCUMENT_UPLOAD'
        elif self.payment_status != 'COMPLETED':
            self.current_step = 'PAYMENT'
        elif self.member.role != 'SUPPORTER' and self.club_approval_status != 'COMPLETED':
            self.current_step = 'CLUB_APPROVAL'
        elif self.safa_approval_status != 'COMPLETED':
            self.current_step = 'SAFA_APPROVAL'
        else:
            self.current_step = 'COMPLETE'

        self.save()

    def get_next_required_actions(self):
        """Get list of actions needed to progress registration"""
        actions = []

        if self.personal_info_status != 'COMPLETED':
            actions.append(_("Complete personal information"))
        if self.club_selection_status != 'COMPLETED':
            actions.append(_("Select a club"))
        if self.document_upload_status != 'COMPLETED':
            actions.append(_("Upload required documents"))
        if self.payment_status != 'COMPLETED':
            actions.append(_("Complete payment"))
        if self.club_approval_status == 'BLOCKED':
            actions.append(_("Contact club for approval status"))
        if self.safa_approval_status == 'BLOCKED':
            actions.append(_("Contact SAFA for approval status"))

        return actions


class MemberSeasonHistory(TimeStampedModel):
    """
    Track member's history across seasons
    Maintains complete historical record of member's club affiliations and status
    """
    member = models.ForeignKey(
        'membership.Member',  # Use consistent string reference
        on_delete=models.CASCADE,
        related_name='season_history'
    )
    season_config = models.ForeignKey(
        SAFASeasonConfig,
        on_delete=models.CASCADE,
        related_name='member_histories'
    )

    # Status during this season
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=MEMBERSHIP_STATUS
    )

    # Club affiliation during this season
    club = models.ForeignKey(
        'geography.Club',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='historical_members'
    )

    # Geographic affiliations during this season
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

    # Associations during this season (for officials)
    associations = models.ManyToManyField(
        'geography.Association',
        blank=True,
        related_name='historical_member_officials'
    )

    # Registration details for this season
    registration_date = models.DateTimeField()
    registration_method = models.CharField(
        _("Registration Method"),
        max_length=10,
        choices=Member.REGISTRATION_METHODS
    )

    # Payment and approval details
    invoice_paid = models.BooleanField(_("Invoice Paid"), default=False)
    safa_approved = models.BooleanField(_("SAFA Approved"), default=False)
    safa_approved_date = models.DateTimeField(null=True, blank=True)

    # Season-specific details
    jersey_number = models.PositiveIntegerField(null=True, blank=True)
    position = models.CharField(_("Position"), max_length=50, blank=True)

    # Transfer tracking
    transferred_from_club = models.ForeignKey(
        'geography.Club',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='transferred_from_members'
    )
    transfer_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Member Season History")
        verbose_name_plural = _("Member Season Histories")
        unique_together = [('member', 'season_config')]
        ordering = ['-season_config__season_year']
        indexes = [
            models.Index(fields=['member', 'season_config']),
            models.Index(fields=['season_config', 'status']),
            models.Index(fields=['club', 'season_config']),
        ]

    def __str__(self):
        club_name = self.club.name if self.club else 'No Club'
        return f"{self.member.get_full_name()} - Season {self.season_config.season_year} - {club_name}"


class MemberProfile(models.Model):
    """Extended profile for role-specific information"""
    member = models.OneToOneField(
        'membership.Member',  # Use consistent string reference
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # Player-specific fields
    player_position = models.CharField(
        _("Playing Position"),
        max_length=50,
        blank=True,
        choices=[
            ('GK', 'Goalkeeper'),
            ('DF', 'Defender'),
            ('MF', 'Midfielder'),
            ('FW', 'Forward'),
        ]
    )

    # Official-specific fields
    official_position = models.ForeignKey(
        'accounts.Position',  # String reference to avoid circular imports
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='member_profiles'
    )
    certification_number = models.CharField(
        _("Certification Number"),
        max_length=50,
        blank=True
    )
    certification_document = models.FileField(
        _("Certification Document"),
        upload_to='certification_documents/',
        blank=True, null=True
    )
    certification_expiry_date = models.DateField(
        _("Certification Expiry Date"),
        blank=True, null=True
    )
    referee_level = models.CharField(
        _("Referee Level"),
        max_length=20,
        blank=True,
        choices=[
            ('LOCAL', 'Local'),
            ('REGIONAL', 'Regional'),
            ('PROVINCIAL', 'Provincial'),
            ('NATIONAL', 'National'),
            ('INTERNATIONAL', 'International'),
        ]
    )

    # Guardian information for juniors
    guardian_name = models.CharField(_("Guardian Name"), max_length=100, blank=True)
    guardian_email = models.EmailField(_("Guardian Email"), blank=True)
    guardian_phone = models.CharField(_("Guardian Phone"), max_length=20, blank=True)
    birth_certificate = models.ImageField(
        _("Birth Certificate"),
        upload_to='documents/birth_certificates/',
        null=True, blank=True
    )

    class Meta:
        verbose_name = _("Member Profile")
        verbose_name_plural = _("Member Profiles")

    def __str__(self):
        return f"Profile for {self.member.get_full_name()}"


class Invoice(TimeStampedModel):
    """Universal Invoice model for organizations and members"""
    INVOICE_STATUS = [
        ('DRAFT', _('Draft')),
        ('PENDING', _('Pending Payment')),
        ('PENDING_REVIEW', _('Pending Review (Proof Submitted)')), # New status
        ('PAID', _('Fully Paid')),
        ('OVERDUE', _('Overdue')),
        ('CANCELLED', _('Cancelled')),
        ('PARTIALLY_PAID', _('Partially Paid')),
    ]

    INVOICE_TYPES = [
        ('ORGANIZATION_MEMBERSHIP', _('Organization Membership Fee')),
        ('MEMBER_REGISTRATION', _('Member Registration Fee')),
        ('ANNUAL_FEE', _('Annual Membership Fee')),
        ('RENEWAL', _('Season Renewal')),
        ('OTHER', _('Other')),
    ]

    # Identifiers
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invoice_number = models.CharField(_("Invoice Number"), max_length=50, unique=True, blank=True)

    # Core relationships
    season_config = models.ForeignKey(
        SAFASeasonConfig,
        on_delete=models.PROTECT,
        related_name='invoices',
        null=True, blank=True
    )

    # For member invoices
    member = models.ForeignKey(
        'membership.Member',  # Use consistent string reference
        on_delete=models.CASCADE,
        related_name='invoices',
        null=True, blank=True
    )

    # For organization invoices - generic foreign key
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    organization = GenericForeignKey('content_type', 'object_id')

    # Invoice details
    status = models.CharField(_("Status"), max_length=20, choices=INVOICE_STATUS, default='PENDING')
    invoice_type = models.CharField(_("Invoice Type"), max_length=30, choices=INVOICE_TYPES)

    # Financial details
    subtotal = models.DecimalField(
        _("Subtotal (Excl. VAT)"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    vat_rate = models.DecimalField(
        _("VAT Rate"),
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.1500')
    )
    vat_amount = models.DecimalField(
        _("VAT Amount"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_amount = models.DecimalField(
        _("Total Amount (Incl. VAT)"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
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

    # Payment plan support
    is_payment_plan = models.BooleanField(
        _("Payment Plan"),
        default=False,
        help_text=_("Allow payment in installments")
    )
    installments = models.PositiveIntegerField(
        _("Number of Installments"),
        default=1
    )

    # Dates
    issue_date = models.DateField(_("Issue Date"), default=date.today)
    due_date = models.DateField(_("Due Date"), null=True, blank=True)
    payment_date = models.DateTimeField(_("Payment Date"), null=True, blank=True)

    # Payment details
    PAYMENT_METHODS = [
        ('EFT', _('Electronic Funds Transfer')),
        ('CASH', _('Cash')),
        ('CARD', _('Credit/Debit Card')),
        ('CHEQUE', _('Cheque')),
        ('ONLINE', _('Online Payment')),
        ('MOBILE', _('Mobile Payment')),
        ('OTHER', _('Other')),
        ('BANK_TRANSFER', _('Bank Transfer')),
    ]

    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True, choices=PAYMENT_METHODS)
    payment_reference = models.CharField(_("Payment Reference"), max_length=100, blank=True)
    proof_of_payment = models.FileField(
        _("Proof of Payment"),
        upload_to='payment_proofs/%Y/%m/',
        null=True, blank=True,
        help_text=_("Upload proof of payment document or receipt")
    )

    payment_submitted_by = models.ForeignKey( # New field
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='submitted_invoice_payments',
        help_text=_("User who submitted the proof of payment")
    )
    payment_submission_date = models.DateTimeField( # New field
        _("Payment Submission Date"),
        null=True, blank=True,
        help_text=_("Date and time when proof of payment was submitted")
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
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['season_config', 'status']),
            models.Index(fields=['member', 'status']),
            models.Index(fields=['invoice_type', 'status']),
        ]

    def __str__(self):
        if self.member:
            entity_name = self.member.get_full_name()
        elif self.organization:
            entity_name = getattr(self.organization, 'name', str(self.organization))
        else:
            entity_name = "Unknown"
        
        # Ensure total_amount is a Decimal before formatting
        total_amount_decimal = Decimal(self.total_amount) if not isinstance(self.total_amount, Decimal) else self.total_amount
        return f"INV-{self.invoice_number} - {entity_name} - R{total_amount_decimal}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()

        # Calculate totals
        # Determine if VAT needs to be reverse-calculated
        # This logic applies if total_amount is set, but subtotal is not,
        # and it's an organization/admin related invoice type.
        is_reverse_vat_calculation = (
            self.total_amount is not None and
            self.subtotal is None and
            self.invoice_type in ['ORGANIZATION_MEMBERSHIP', 'ANNUAL_FEE', 'MEMBER_REGISTRATION'] # Assuming these are for administrators/organizations
        )

        if is_reverse_vat_calculation:
            # Calculate subtotal from total_amount (total / (1 + vat_rate))
            self.subtotal = (self.total_amount / (Decimal('1') + self.vat_rate)).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            # Calculate vat_amount (total_amount - subtotal)
            self.vat_amount = (self.total_amount - self.subtotal).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        elif self.subtotal is not None: # Original calculation if subtotal is provided
            self.vat_amount = (self.subtotal * self.vat_rate).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            self.total_amount = self.subtotal + self.vat_amount
        # else: if neither subtotal nor total_amount is set, they remain as default 0.00

        self.outstanding_amount = self.total_amount - self.paid_amount # This line should always be after total_amount is set

        # Set due date if not set
        if not self.due_date:
            days = self.season_config.payment_due_days if self.season_config else 30
            self.due_date = self.issue_date + timedelta(days=days)

        # Update status based on payment
        if self.paid_amount >= self.total_amount:
            self.status = 'PAID'
            if not self.payment_date:
                self.payment_date = timezone.now()
        elif self.paid_amount > 0:
            self.status = 'PARTIALLY_PAID'
        elif self.due_date and self.due_date < timezone.now().date() and self.status == 'PENDING':
            self.status = 'OVERDUE'

        super().save(*args, **kwargs)

    def generate_invoice_number(self):
        """Generate unique invoice number in MEM-YYYYMMDD/safa_id-XX format"""
        today_str = timezone.now().strftime("%Y%m%d")
        
        # Ensure the invoice is associated with a member to get safa_id
        if not self.member or not self.member.safa_id:
            # Fallback to a generic unique number if member or safa_id is missing
            year = self.season_config.season_year if self.season_config else timezone.now().year
            import random
            import string
            prefix = f"MEM{year}"
            while True:
                suffix = ''.join(random.choices(string.digits, k=6))
                number = f"{prefix}{suffix}"
                if not Invoice.objects.filter(invoice_number=number).exists():
                    return number

        base_invoice_number = f"MEM-{today_str}/{self.member.safa_id}"
        
        # Check for existing invoices with the same base number and add a counter
        counter = 0
        while True:
            if counter == 0:
                invoice_number = base_invoice_number
            else:
                invoice_number = f"{base_invoice_number}-{counter:02d}" # Add -01, -02 etc.

            if not Invoice.objects.filter(invoice_number=invoice_number).exists():
                return invoice_number
            counter += 1

    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        if self.due_date and self.status in ['PENDING', 'PARTIALLY_PAID']:
            return timezone.now().date() > self.due_date
        return False

    @property
    def payment_percentage(self):
        """Calculate payment percentage"""
        if self.total_amount > 0:
            return (self.paid_amount / self.total_amount * 100)
        return 0

    def mark_as_paid(self, payment_method='', payment_reference=''):
        """Mark invoice as paid and trigger activation"""
        if self.status != 'PAID':
            self.status = 'PAID'
            self.payment_date = timezone.now()
            self.paid_amount = self.total_amount
            self.outstanding_amount = Decimal('0.00')
            self.payment_method = payment_method
            self.payment_reference = payment_reference
            self.save()

            # Create/update season history when invoice is paid
            if self.member:
                self.create_or_update_season_history()

                # ADDED: Update registration workflow
                try:
                    workflow = self.member.workflow
                    if workflow.current_step == 'PAYMENT':
                        workflow.payment_status = 'COMPLETED'
                        workflow.current_step = 'SAFA_APPROVAL'
                        workflow.save()
                except RegistrationWorkflow.DoesNotExist:
                    # If no workflow exists, create one and set it to the approval step
                    RegistrationWorkflow.objects.create(
                        member=self.member,
                        payment_status='COMPLETED',
                        current_step='SAFA_APPROVAL'
                    )

    def create_or_update_season_history(self):
        """Create or update season history when member invoice is paid"""
        if not self.member:
            return

        history, created = MemberSeasonHistory.objects.get_or_create(
            member=self.member,
            season_config=self.season_config,
            defaults={
                'status': self.member.status,
                'club': self.member.current_club,
                'province': self.member.province,
                'region': self.member.region,
                'lfa': self.member.lfa,
                'registration_date': self.member.created,
                'registration_method': self.member.registration_method,
                'invoice_paid': True,
                'safa_approved': self.member.status == 'ACTIVE',
                'safa_approved_date': timezone.now()
            }
        )

        if not created:
            # Update existing history record
            history.club = self.member.current_club
            history.province = self.member.province
            history.region = self.member.region
            history.lfa = self.member.lfa
            history.status = self.member.status
            history.registration_date = self.member.created
            history.registration_method = self.member.registration_method
            history.invoice_paid = True
            history.safa_approved = self.member.status == 'ACTIVE'
            history.safa_approved_date = timezone.now()
            history.save()

    @classmethod
    def create_member_invoice(cls, member):
        """Create invoice for member registration"""
        try:
            print(f"🔍 DEBUG: Creating REGULAR invoice for member {member.safa_id} using COMPLEX calculation")
            
            # Ensure member has a current season
            if not member.current_season:
                member.current_season = SAFASeasonConfig.get_active_season()
                if not member.current_season:
                    print(f"❌ No active season found for member {member.safa_id}")
                    return None
                member.save()
            
            # Determine fee based on user role
            fee_amount = member.calculate_registration_fee()
            print(f"🔍 DEBUG: Complex calculation result: R{fee_amount}")

            if fee_amount > 0:
                invoice = cls.objects.create(
                    member=member,
                    invoice_type='MEMBER_REGISTRATION',
                    total_amount=fee_amount,
                    subtotal=fee_amount,
                    season_config=member.current_season,
                    status='PENDING',
                    payment_method='Cash or EFT'
                )
                
                # Create invoice item
                InvoiceItem.objects.create(
                    invoice=invoice,
                    description=f"SAFA {member.get_role_display()} Registration Fee - {member.current_season.season_year} (Complex Calculation)",
                    unit_price=fee_amount,
                    quantity=1,
                    total_price=fee_amount,
                    amount=fee_amount
                )
                
                print(f"🔍 DEBUG: Created REGULAR invoice {invoice.invoice_number} with amount R{fee_amount}")
                return invoice
        except Exception as e:
            print(f"Error creating invoice: {e}")
            raise

    @classmethod
    def create_simple_member_invoice(cls, member):
        """Create invoice for member registration using the specific formula: Fee = Total / 1.15, VAT = Fee * 15%"""
        try:
            print(f"🔍 DEBUG: Creating SIMPLE invoice for member {member.safa_id} using YOUR FORMULA")
            
            # Ensure member has a current season
            if not member.current_season:
                member.current_season = SAFASeasonConfig.get_active_season()
                if not member.current_season:
                    print(f"❌ No active season found for member {member.safa_id}")
                    return None
                member.save()
            
            # Get the fee excluding VAT using the specific formula
            fee_excluding_vat = member.calculate_simple_registration_fee()
            print(f"🔍 DEBUG: Simple calculation - Fee (excl. VAT): R{fee_excluding_vat}")
            
            if fee_excluding_vat > 0:
                # Calculate VAT amount: Fee * 15%
                vat_amount = fee_excluding_vat * Decimal('0.15')
                print(f"🔍 DEBUG: Simple calculation - VAT (15%): R{vat_amount}")
                
                # Total amount is the original annual fee (R200)
                total_amount = fee_excluding_vat + vat_amount
                print(f"🔍 DEBUG: Simple calculation - Total: R{total_amount}")
                
                # Create invoice with proper VAT breakdown
                invoice = cls.objects.create(
                    member=member,
                    invoice_type='MEMBER_REGISTRATION',
                    subtotal=fee_excluding_vat,  # R173.91 (excl. VAT)
                    vat_amount=vat_amount,       # R26.09 (15% VAT)
                    total_amount=total_amount,   # R200.00 (incl. VAT)
                    season_config=member.current_season,
                    status='PENDING',
                    payment_method='Cash or EFT'
                )
                
                # Create invoice item
                InvoiceItem.objects.create(
                    invoice=invoice,
                    description=f"SAFA {member.get_role_display()} Registration Fee - {member.current_season.season_year} (Simple Formula)",
                    unit_price=fee_excluding_vat,  # Unit price excluding VAT
                    quantity=1,
                    total_price=fee_excluding_vat,  # Total price excluding VAT
                    amount=total_amount  # Total amount including VAT
                )
                
                print(f"🔍 DEBUG: Created SIMPLE invoice {invoice.invoice_number} with breakdown: Subtotal R{fee_excluding_vat}, VAT R{vat_amount}, Total R{total_amount}")
                return invoice
        except Exception as e:
            print(f"Error creating simple invoice: {e}")
            raise


class InvoiceItem(models.Model):
    """Line items for invoices (membership fees, registrations, etc.)"""
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    description = models.CharField(_("Description"), max_length=255)
    unit_price = models.DecimalField(_("Unit Price (Excl. VAT)"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    total_price = models.DecimalField(_("Total Price (Excl. VAT)"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    amount = models.DecimalField(_("Amount (Incl. VAT)"), max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")

    def __str__(self):
        # Ensure self.amount is a Decimal
        amount_decimal = Decimal(self.amount) if not isinstance(self.amount, Decimal) else self.amount
        return f"{self.description} - R{amount_decimal} x{self.quantity}"

    def save(self, *args, **kwargs):
        # Auto-calculate total price (excl. VAT)
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
    
    @property
    def sub_total(self):
        """Property to provide sub_total for template compatibility"""
        return self.total_price