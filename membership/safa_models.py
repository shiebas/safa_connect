# membership/safa_models.py
# SAFA-specific models that work alongside existing models

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from model_utils.models import TimeStampedModel
from decimal import Decimal, ROUND_HALF_UP
import uuid

# Import your existing models WITHOUT touching them
from .models import Member


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
        'accounts.CustomUser',
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
        db_table = 'safa_season_config'
    
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
        # Fallback to current year if no active season
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
        'accounts.CustomUser',
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
        db_table = 'safa_fee_structure'
    
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


class SAFAInvoice(TimeStampedModel):
    """
    Enhanced Invoice model with VAT compliance and partial payment support
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
        ('PENALTY', _('Penalty/Fine')),
        ('EVENT', _('Event Fee')),
        ('TRANSFER_FEE', _('Transfer Fee')),
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
    
    # Season reference
    season_config = models.ForeignKey(
        SAFASeasonConfig,
        on_delete=models.PROTECT,
        related_name='safa_invoices',
        help_text=_("Season this invoice belongs to")
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
        default='REGISTRATION'
    )
    
    # Link to your existing Member model
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='safa_invoices',
        null=True, blank=True,
        help_text=_("Member this invoice is for")
    )
    
    # Organizations using ContentType for flexibility
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        null=True, blank=True,
        help_text=_("Type of organization (Club, LFA, etc.)")
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    organization = GenericForeignKey('content_type', 'object_id')
    
    # Financial details (all amounts exclude VAT)
    subtotal = models.DecimalField(
        _("Subtotal (Excl. VAT)"), 
        max_digits=12, 
        decimal_places=2,
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
    due_date = models.DateField(_("Due Date"))
    payment_date = models.DateTimeField(_("Payment Date"), null=True, blank=True)
    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True)
    payment_reference = models.CharField(_("Payment Reference"), max_length=100, blank=True)
    
    # Pro-rata information
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
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        related_name='issued_safa_invoices',
        null=True, blank=True
    )
    
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("SAFA Invoice")
        verbose_name_plural = _("SAFA Invoices")
        ordering = ['-issue_date', '-created']
        db_table = 'safa_invoice'
    
    def __str__(self):
        return f"SAFA-{self.invoice_number} - R{self.total_amount}"
    
    def save(self, *args, **kwargs):
        # Generate invoice number if not set
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        
        # Calculate VAT and totals
        self.calculate_totals()
        
        # Set due date if not set
        if not self.due_date:
            from datetime import timedelta
            days = self.season_config.payment_due_days if self.season_config else 30
            self.due_date = self.issue_date + timedelta(days=days)
        
        # Calculate outstanding amount
        self.outstanding_amount = self.total_amount - self.paid_amount
        
        # Update status based on payment
        self.update_payment_status()
        
        super().save(*args, **kwargs)
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        year = self.season_config.season_year if self.season_config else timezone.now().year
        return f"SAFA{year}{timezone.now().strftime('%m%d')}{str(self.pk or 1).zfill(4)}"
    
    def calculate_totals(self):
        """Calculate VAT and total amounts"""
        if self.subtotal:
            self.vat_amount = (self.subtotal * self.vat_rate).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            self.total_amount = self.subtotal + self.vat_amount
    
    def update_payment_status(self):
        """Update invoice status based on payment amount"""
        if self.paid_amount >= self.total_amount:
            self.status = 'PAID'
            if not self.payment_date:
                self.payment_date = timezone.now()
        elif self.paid_amount > 0:
            self.status = 'PARTIALLY_PAID'
        elif self.due_date < timezone.now().date() and self.status == 'PENDING':
            self.status = 'OVERDUE'
    
    def add_payment(self, amount, payment_method='', payment_reference='', processed_by=None):
        """Add a payment to this invoice"""
        amount = Decimal(str(amount))
        
        # Create payment record
        payment = SAFAInvoicePayment.objects.create(
            safa_invoice=self,
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
        """Activate member when invoice is fully paid"""
        if self.member and hasattr(self.member, 'status'):
            self.member.status = 'ACTIVE'
            self.member.save()
    
    @property
    def is_paid(self):
        """Check if invoice is fully paid"""
        return self.status == 'PAID'
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        return self.status == 'OVERDUE' or (
            self.status in ['PENDING', 'PARTIALLY_PAID'] and 
            self.due_date < timezone.now().date()
        )
    
    @property
    def payment_percentage(self):
        """Calculate payment percentage"""
        if self.total_amount > 0:
            return (self.paid_amount / self.total_amount * 100).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        return Decimal('0.00')


class SAFAInvoicePayment(TimeStampedModel):
    """Track individual payments against SAFA invoices"""
    PAYMENT_METHODS = [
        ('EFT', _('Electronic Funds Transfer')),
        ('CASH', _('Cash')),
        ('CARD', _('Credit/Debit Card')),
        ('CHEQUE', _('Cheque')),
        ('ONLINE', _('Online Payment')),
        ('MOBILE', _('Mobile Payment')),
        ('OTHER', _('Other')),
    ]
    
    safa_invoice = models.ForeignKey(
        SAFAInvoice, 
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
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='processed_safa_payments'
    )
    
    notes = models.TextField(_("Payment Notes"), blank=True)
    
    class Meta:
        verbose_name = _("SAFA Invoice Payment")
        verbose_name_plural = _("SAFA Invoice Payments")
        ordering = ['-payment_date']
        db_table = 'safa_invoice_payment'
    
    def __str__(self):
        return f"Payment R{self.amount} - {self.safa_invoice.invoice_number}"