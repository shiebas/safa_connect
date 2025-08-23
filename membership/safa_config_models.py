# membership/config_models.py
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

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
    
    # Registration periods
    organization_registration_start = models.DateField(
        _("Organization Registration Start"),
        help_text=_("When organizations can start paying membership fees")
    )
    organization_registration_end = models.DateField(
        _("Organization Registration End"),
        help_text=_("Deadline for organization membership payments")
    )
    member_registration_start = models.DateField(
        _("Member Registration Start"),
        help_text=_("When individual members can start registering")
    )
    member_registration_end = models.DateField(
        _("Member Registration End"),
        help_text=_("Deadline for individual member registrations")
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
    
    is_organization = models.BooleanField(_("Is Organization"), default=False)

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
    
    def __str__(self):
        return f"{self.get_entity_type_display()} - R{self.annual_fee} ({self.season_config.season_year})"
    
    def save(self, *args, **kwargs):
        self.is_organization = self.entity_type in ['ASSOCIATION', 'PROVINCE', 'REGION', 'LFA', 'CLUB']
        super().save(*args, **kwargs)

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


class SAFAPaymentPlan(models.Model):
    """
    Payment plan configurations for installment payments
    """
    PAYMENT_FREQUENCIES = [
        ('MONTHLY', _('Monthly')),
        ('QUARTERLY', _('Quarterly')),
        ('BIANNUAL', _('Bi-Annual')),
        ('ANNUAL', _('Annual')),
    ]
    
    season_config = models.ForeignKey(
        SAFASeasonConfig,
        on_delete=models.CASCADE,
        related_name='payment_plans'
    )
    
    name = models.CharField(
        _("Plan Name"),
        max_length=100,
        help_text=_("e.g., 'Monthly Payment Plan', 'Quarterly Plan'")
    )
    
    frequency = models.CharField(
        _("Payment Frequency"),
        max_length=20,
        choices=PAYMENT_FREQUENCIES
    )
    
    number_of_installments = models.PositiveIntegerField(
        _("Number of Installments"),
        help_text=_("How many payments in total")
    )
    
    installment_fee = models.DecimalField(
        _("Installment Processing Fee"),
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Additional fee per installment for processing")
    )
    
    is_available_for_organizations = models.BooleanField(
        _("Available for Organizations"),
        default=True,
        help_text=_("Whether organizations (clubs, LFAs, etc.) can use this plan")
    )
    
    is_available_for_individuals = models.BooleanField(
        _("Available for Individuals"),
        default=True,
        help_text=_("Whether individuals (players, officials) can use this plan")
    )
    
    minimum_amount = models.DecimalField(
        _("Minimum Invoice Amount"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Minimum invoice amount to qualify for this payment plan")
    )
    
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("SAFA Payment Plan")
        verbose_name_plural = _("SAFA Payment Plans")
        ordering = ['season_config', 'number_of_installments']
    
    def __str__(self):
        return f"{self.name} ({self.season_config.season_year})"


class SAFAInvoiceSequence(models.Model):
    """
    Manages invoice numbering sequences per season
    """
    season_config = models.OneToOneField(
        SAFASeasonConfig,
        on_delete=models.CASCADE,
        related_name='invoice_sequence'
    )
    
    prefix = models.CharField(
        _("Invoice Prefix"),
        max_length=10,
        default="SAFA",
        help_text=_("Prefix for invoice numbers (e.g., SAFA, INV)")
    )
    
    current_number = models.PositiveIntegerField(
        _("Current Number"),
        default=1,
        help_text=_("Current invoice number (will be incremented)")
    )
    
    number_length = models.PositiveIntegerField(
        _("Number Length"),
        default=6,
        help_text=_("Total length of number part (padded with zeros)")
    )
    
    class Meta:
        verbose_name = _("SAFA Invoice Sequence")
        verbose_name_plural = _("SAFA Invoice Sequences")
    
    def __str__(self):
        return f"Invoice Sequence {self.season_config.season_year}"
    
    def get_next_invoice_number(self):
        """Generate next invoice number and increment counter"""
        invoice_number = f"{self.prefix}{self.season_config.season_year}{str(self.current_number).zfill(self.number_length)}"
        self.current_number += 1
        self.save(update_fields=['current_number'])
        return invoice_number


class SAFAInvoiceTemplate(models.Model):
    """
    Templates for different types of invoices
    """
    TEMPLATE_TYPES = [
        ('REGISTRATION', _('Registration Invoice')),
        ('ANNUAL_FEE', _('Annual Membership Fee')),
        ('RENEWAL', _('Season Renewal')),
        ('PENALTY', _('Penalty/Fine')),
        ('EVENT', _('Event Fee')),
        ('OTHER', _('Other')),
    ]
    
    template_type = models.CharField(
        _("Template Type"),
        max_length=20,
        choices=TEMPLATE_TYPES,
        unique=True
    )
    
    subject_template = models.CharField(
        _("Email Subject Template"),
        max_length=200,
        help_text=_("Template for email subject. Use {variables} for dynamic content.")
    )
    
    email_body_template = models.TextField(
        _("Email Body Template"),
        help_text=_("Template for email body. Use {variables} for dynamic content.")
    )
    
    sms_template = models.TextField(
        _("SMS Template"),
        blank=True,
        max_length=160,
        help_text=_("Template for SMS notifications (max 160 characters)")
    )
    
    description_template = models.CharField(
        _("Invoice Description Template"),
        max_length=500,
        help_text=_("Template for invoice line item descriptions")
    )
    
    is_active = models.BooleanField(_("Active"), default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("SAFA Invoice Template")
        verbose_name_plural = _("SAFA Invoice Templates")
    
    def __str__(self):
        return f"{self.get_template_type_display()} Template"