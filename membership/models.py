# membership/models.py - CORRECTED and Complete Implementation

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from model_utils.models import TimeStampedModel
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from decimal import Decimal, ROUND_HALF_UP
import uuid
import re
from datetime import date, timedelta

# Conditional GIS import (avoid errors if PostGIS not set up)
try:
    from django.contrib.gis.db import models as gis_models
    from django.contrib.gis.geos import Point
    GIS_AVAILABLE = True
except ImportError:
    # Fallback if GIS not available
    gis_models = models
    Point = None
    GIS_AVAILABLE = False

# Conditional geocoder import
try:
    import geocoder
    GEOCODER_AVAILABLE = True
except ImportError:
    GEOCODER_AVAILABLE = False


class SAFASeasonConfig(models.Model):
    """Configuration for SAFA seasons and fee structures"""
    season_year = models.PositiveIntegerField(
        _("Season Year"), 
        unique=True,
        help_text=_("The year this season configuration applies to (e.g., 2025)")
    )
    
    season_start_date = models.DateField(_("Season Start Date"))
    season_end_date = models.DateField(_("Season End Date"))
    
    # Registration periods
    organization_registration_start = models.DateField(
        _("Organization Registration Start"),
        help_text=_("When organizations can start paying membership fees"),
        default=date(2020, 1, 1) # Default for existing rows
    )
    organization_registration_end = models.DateField(
        _("Organization Registration End"),
        help_text=_("Deadline for organization membership payments"),
        default=date(2099, 12, 31) # Default for existing rows
    )
    member_registration_start = models.DateField(
        _("Member Registration Start"),
        help_text=_("When individual members can start registering"),
        default=date(2020, 1, 1) # Default for existing rows
    )
    member_registration_end = models.DateField(
        _("Member Registration End"),
        help_text=_("Deadline for individual member registrations"),
        default=date(2099, 12, 31) # Default for existing rows
    )
    
    vat_rate = models.DecimalField(
        _("VAT Rate"), 
        max_digits=5, 
        decimal_places=4, 
        default=Decimal('0.1500')
    )
    
    payment_due_days = models.PositiveIntegerField(_("Payment Due Days"), default=30)
    
    is_active = models.BooleanField(_("Active Season"), default=False)
    is_renewal_season = models.BooleanField(
        _("Renewal Season"), 
        default=False,
        help_text=_("Generates invoices for all entities when activated")
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_season_configs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("SAFA Season Configuration")
        verbose_name_plural = _("SAFA Season Configurations")
        ordering = ['-season_year']
        indexes = [
            models.Index(fields=['season_year']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        status = "ACTIVE" if self.is_active else "INACTIVE"
        return f"SAFA Season {self.season_year} ({status})"
    
    def save(self, *args, **kwargs):
        if self.is_active:
            SAFASeasonConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_season(cls):
        return cls.objects.filter(is_active=True).first()
    
    @property
    def organization_registration_open(self):
        """Check if organization registration is currently open"""
        today = timezone.now().date()
        return self.organization_registration_start <= today <= self.organization_registration_end
    
    @property
    def member_registration_open(self):
        """Check if member registration is currently open"""
        today = timezone.now().date()
        return self.member_registration_start <= today <= self.member_registration_end


class SAFAFeeStructure(models.Model):
    """Fee structure for different entity types - organizations and members"""
    ENTITY_TYPES = [
        # Organizations (must pay first)
        ('ASSOCIATION', _('Association')),
        ('PROVINCE', _('Province')),
        ('REGION', _('Region')),
        ('LFA', _('Local Football Association')),
        ('CLUB', _('Club')),
        
        # Individual Members (can only register after org is paid)
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
    entity_type = models.CharField(_("Entity Type"), max_length=30, choices=ENTITY_TYPES)
    annual_fee = models.DecimalField(_("Annual Fee (Excl. VAT)"), max_digits=10, decimal_places=2)
    description = models.TextField(_("Fee Description"), blank=True)
    is_pro_rata = models.BooleanField(_("Pro-rata Applicable"), default=True)
    minimum_fee = models.DecimalField(
        _("Minimum Fee (Excl. VAT)"), 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    is_organization = models.BooleanField(_("Is Organization"), default=False)
    requires_organization_payment = models.BooleanField(_("Requires Organization Payment"), default=True)
    
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
        indexes = [
            models.Index(fields=['season_config', 'entity_type']),
            models.Index(fields=['is_organization']),
        ]
    
    def __str__(self):
        return f"{self.description} (x{self.quantity})"
    
    @property
    def sub_total(self):
        return self.quantity * self.unit_price


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
        'Member', 
        on_delete=models.CASCADE, 
        related_name='transfers',
        null=True, blank=True # Temporarily allow nulls for migration
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
    member = models.OneToOneField('Member', on_delete=models.CASCADE, related_name='legacy_membership')
    membership_type = models.CharField(max_length=20, default='STANDARD')
    
    class Meta:
        verbose_name = _("Legacy Membership")
        verbose_name_plural = _("Legacy Memberships")
    
    def __str__(self):
        return f"Legacy: {self.member.get_full_name()}"


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
        on_delete=models.CASCADE, null = True, 
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


class Member(TimeStampedModel):
    """
    Centralized Member model - handles all member types (players, officials, etc.)
    """
    
    MEMBER_ROLES = [
        ('PLAYER', _('Player')),
        ('OFFICIAL', _('Official')),
        ('ADMIN', _('Administrator')),
    ]

    MEMBERSHIP_STATUS = [
        ('PENDING', _('Pending SAFA Approval')),
        ('ACTIVE', _('SAFA Approved - Active')),
        ('INACTIVE', _('Inactive')),
        ('SUSPENDED', _('Suspended')),
        ('REJECTED', _('Rejected by SAFA')),
        ('TRANSFERRED', _('Transferred from another club')),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    DOCUMENT_TYPES = (
        ('BC', _('Birth Certificate')),
        ('PP', _('Passport')),
        ('ID', _('National ID')),
        ('DL', _('Driver License')),
        ('OT', _('Other')),
    )

    # Link to the authentication user
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='member_profile'
    )

    # Personal Information
    middle_name = models.CharField(max_length=100, blank=True)
    alias = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    nationality = models.CharField(max_length=50, default='South African')
    birth_country = models.CharField(max_length=3, default='ZAF')
    
    # Identification
    id_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    passport_number = models.CharField(max_length=25, blank=True, null=True, unique=True)
    id_document_type = models.CharField(max_length=2, choices=DOCUMENT_TYPES, default='ID')
    
    # SAFA specific
    safa_id = models.CharField(max_length=5, unique=True, blank=True, null=True)
    fifa_id = models.CharField(max_length=7, unique=True, blank=True, null=True)
    
    # Contact
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Address
    street_address = models.CharField(max_length=255, blank=True)
    suburb = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default='South Africa')

    # Media
    profile_photo = models.ImageField(upload_to='images/profile_photos/', blank=True, null=True)
    id_document = models.FileField(upload_to='documents/user_documents/', null=True, blank=True)

    # Compliance
    popi_act_consent = models.BooleanField(default=False)

    # Membership Status
    membership_status = models.CharField(max_length=20, choices=MEMBERSHIP_STATUS, default='PENDING')
    
    # Geographical and Organizational relationships
    national_federation = models.ForeignKey('geography.NationalFederation', on_delete=models.SET_NULL, null=True, blank=True)
    province = models.ForeignKey('geography.Province', on_delete=models.SET_NULL, null=True, blank=True)
    region = models.ForeignKey('geography.Region', on_delete=models.SET_NULL, null=True, blank=True)
    lfa = models.ForeignKey('geography.LocalFootballAssociation', on_delete=models.SET_NULL, null=True, blank=True)
    club = models.ForeignKey('geography.Club', on_delete=models.SET_NULL, null=True, blank=True)
    association = models.ForeignKey('geography.Association', on_delete=models.SET_NULL, null=True, blank=True)

    # Player specific fields
    position = models.CharField(max_length=50, blank=True)
    jersey_number = models.PositiveIntegerField(null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = _("Member")
        verbose_name_plural = _("Members")

    def __str__(self):
        return self.user.get_full_name()

class OfficialCertification(TimeStampedModel):
    """
    Tracks certification history for officials (referees, coaches, etc.)
    Allows recording multiple certifications with dates obtained
    """
    CERTIFICATION_TYPES = [
        ('REFEREE', _('Referee Certification')),
        ('COACH', _('Coaching Certification')),
        ('ADMIN', _('Administrative Certification')),
        ('OTHER', _('Other Certification')),
    ]

    LEVEL_CHOICES = [
        ('LOCAL', _('Local')),
        ('REGIONAL', _('Regional')),
        ('PROVINCIAL', _('Provincial')),
        ('NATIONAL', _('National')),
        ('INTERNATIONAL', _('International')),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE,
                              related_name='certifications',
                              help_text=_("The official who holds this certification"))

    certification_type = models.CharField(_("Certification Type"), max_length=20,
                                       choices=CERTIFICATION_TYPES,
                                       help_text=_("Type of certification"))

    level = models.CharField(_("Level"), max_length=20,
                          choices=LEVEL_CHOICES,
                          help_text=_("Level or grade of the certification"))

    name = models.CharField(_("Certification Name"), max_length=100,
                         help_text=_("Name of the specific certification or qualification"))

    issuing_body = models.CharField(_("Issuing Organization"), max_length=100,
                                 help_text=_("Organization that issued this certification"))

    certification_number = models.CharField(_("Certification Number"), max_length=50,
                                         blank=True, null=True,
                                         help_text=_("Unique identifier for this certification"))

    obtained_date = models.DateField(_("Date Obtained"),
                                  help_text=_("When the certification was first obtained"))

    expiry_date = models.DateField(_("Expiry Date"),
                                blank=True, null=True,
                                help_text=_("When the certification expires (if applicable)"))

    document = models.FileField(_("Certificate Document"),
                             upload_to='certification_documents/history/',
                             blank=True, null=True,
                             help_text=_("Upload proof of certification"))

    notes = models.TextField(_("Notes"), blank=True,
                          help_text=_("Additional information about this certification"))

    is_verified = models.BooleanField(_("Verified"), default=False,
                                   help_text=_("Whether this certification has been verified by an administrator"))

    class Meta:
        verbose_name = _("Official Certification")
        verbose_name_plural = _("Official Certifications")
        ordering = ['-obtained_date']

    def __str__(self):
        return f"{self.member.user.get_full_name()} - {self.name} ({self.level})"

    @property
    def is_active(self):
        """Check if certification is currently active based on expiry date"""
        if not self.expiry_date:
            return True  # Certifications without expiry dates are considered active
        return self.expiry_date >= timezone.now().date()

    @property
    def validity_status(self):
        """Return the validity status of the certification"""
        if not self.is_verified:
            return "Pending Verification"
        if not self.expiry_date:
            return "Active (No Expiration)"
        if self.is_active:
            return "Active"
        return "Expired"



class Invoice(TimeStampedModel):
    """Universal Invoice model for organizations and members"""
    INVOICE_STATUS = [
        ('DRAFT', _('Draft')),
        ('PENDING', _('Pending Payment')),
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
        null=True, blank=True # Temporarily allow nulls for migration
    )
    
    # For member invoices
    member = models.ForeignKey(
        'Member', 
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
    issue_date = models.DateField(_("Issue Date"), default=timezone.now)
    due_date = models.DateField(_("Due Date"), null=True, blank=True)
    payment_date = models.DateTimeField(_("Payment Date"), null=True, blank=True)
    
    # Payment details
    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True)
    payment_reference = models.CharField(_("Payment Reference"), max_length=100, blank=True)
    
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
        return f"INV-{self.invoice_number} - {entity_name} - R{self.total_amount}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        
        # Calculate totals
        if self.subtotal is not None:
            self.vat_amount = (self.subtotal * self.vat_rate).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            self.total_amount = self.subtotal + self.vat_amount
            self.outstanding_amount = self.total_amount - self.paid_amount
        
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
        """Generate unique invoice number"""
        year = self.season_config.season_year if self.season_config else timezone.now().year
        import random
        import string
        
        if self.invoice_type == 'ORGANIZATION_MEMBERSHIP':
            prefix = f"ORG{year}"
        else:
            prefix = f"MEM{year}"
            
        while True:
            suffix = ''.join(random.choices(string.digits, k=6))
            number = f"{prefix}{suffix}"
            if not Invoice.objects.filter(invoice_number=number).exists():
                return number
    
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
                'safa_approved_date': self.member.approved_date,
            }
        )
        
        if not created:
            # Update existing history
            history.invoice_paid = True
            history.save()
        
        # Copy associations for officials
        if self.member.role == 'OFFICIAL':
            history.associations.set(self.member.associations.all())
    
    @classmethod
    def create_member_invoice(cls, member, season_config=None):
        """Create member registration invoice"""
        if not season_config:
            season_config = member.current_season or SAFASeasonConfig.get_active_season()
        
        if not season_config:
            raise ValidationError(_("No active SAFA season configuration found"))
        
        # Get fee structure
        entity_type = member.get_entity_type_for_fees()
        fee_structure = SAFAFeeStructure.objects.filter(
            season_config=season_config,
            entity_type=entity_type
        ).first()
        
        if not fee_structure:
            raise ValidationError(
                f"No fee structure found for {entity_type} in season {season_config.season_year}"
            )
        
        # Create invoice
        invoice = cls.objects.create(
            member=member,
            season_config=season_config,
            invoice_type='MEMBER_REGISTRATION',
            subtotal=fee_structure.annual_fee,
            vat_rate=season_config.vat_rate
        )
        
        # Create line item
        InvoiceItem.objects.create(
            invoice=invoice,
            description=f"SAFA Registration - {fee_structure.get_entity_type_display()}",
            quantity=1,
            unit_price=fee_structure.annual_fee
        )
        
        return invoice
    
    def create_payment_plan(self, installments=3):
        """Create payment plan with multiple invoices"""
        if self.status != 'DRAFT':
            raise ValidationError(_("Can only create payment plan for draft invoices"))
        
        if installments < 2:
            raise ValidationError(_("Payment plan must have at least 2 installments"))
        
        # Calculate installment amounts
        installment_amount = (self.total_amount / installments).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        # Adjust last installment for rounding differences
        last_amount = self.total_amount - (installment_amount * (installments - 1))
        
        # Create installment invoices
        for i in range(installments):
            amount = last_amount if i == installments - 1 else installment_amount
            
            installment_invoice = Invoice.objects.create(
                member=self.member,
                organization=self.organization,
                season_config=self.season_config,
                invoice_type=self.invoice_type,
                subtotal=amount / (1 + self.vat_rate),
                vat_rate=self.vat_rate,
                due_date=self.due_date + timedelta(days=30 * i),
                notes=f"Installment {i+1} of {installments} for {self.invoice_number}"
            )
            
            InvoiceItem.objects.create(
                invoice=installment_invoice,
                description=f"Installment {i+1}/{installments} - {self.items.first().description}",
                quantity=1,
                unit_price=amount / (1 + self.vat_rate)
            )
        
        # Mark original as payment plan
        self.is_payment_plan = True
        self.installments = installments
        self.status = 'CANCELLED'  # Original invoice is replaced by installments
        self.save()


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
        indexes = [
            models.Index(fields=['invoice']),
        ]
    
    def __str__(self):
        return