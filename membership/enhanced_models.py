# membership/enhanced_models.py
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from model_utils.models import TimeStampedModel
from decimal import Decimal, ROUND_HALF_UP
import uuid

class Invoice(TimeStampedModel):
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
    
    PAYMENT_TERMS = [
        (7, _('7 days')),
        (14, _('14 days')),
        (30, _('30 days')),
        (60, _('60 days')),
        (90, _('90 days')),
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
        'SAFASeasonConfig',
        on_delete=models.PROTECT,
        related_name='invoices',
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
    
    # Relationships - Members
    player = models.ForeignKey(
        'registration.Player',
        on_delete=models.CASCADE,
        related_name='player_invoices',
        null=True, blank=True,
        help_text=_("Player this invoice is for")
    )
    
    official = models.ForeignKey(
        'registration.Official',
        on_delete=models.CASCADE,
        related_name='official_invoices',
        null=True, blank=True,
        help_text=_("Official this invoice is for")
    )
    
    # Relationships - Organizations
    club = models.ForeignKey(
        'geography.Club',
        on_delete=models.CASCADE,
        related_name='club_invoices',
        null=True, blank=True
    )
    
    association = models.ForeignKey(
        'geography.Association',
        on_delete=models.CASCADE,
        related_name='association_invoices',
        null=True, blank=True
    )
    
    lfa = models.ForeignKey(
        'geography.LocalFootballAssociation',
        on_delete=models.CASCADE,
        related_name='lfa_invoices',
        null=True, blank=True
    )
    
    region = models.ForeignKey(
        'geography.Region',
        on_delete=models.CASCADE,
        related_name='region_invoices',
        null=True, blank=True
    )
    
    province = models.ForeignKey(
        'geography.Province',
        on_delete=models.CASCADE,
        related_name='province_invoices',
        null=True, blank=True
    )
    
    # Generic foreign key for any other entity
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
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
        help_text=_("VAT amount calculated")
    )
    
    total_amount = models.DecimalField(
        _("Total Amount (Incl. VAT)"), 
        max_digits=12, 
        decimal_places=2,
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
    payment_terms = models.PositiveIntegerField(
        _("Payment Terms (Days)"),
        choices=PAYMENT_TERMS,
        default=30
    )
    
    # Payment details
    payment_date = models.DateTimeField(_("Payment Date"), null=True, blank=True)
    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True)
    payment_reference = models.CharField(
        _("Payment Reference"), 
        max_length=100, 
        blank=True,
        help_text=_("Bank reference or transaction ID")
    )
    
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
        related_name='issued_invoices',
        null=True, blank=True
    )
    
    notes = models.TextField(_("Notes"), blank=True)
    internal_notes = models.TextField(
        _("Internal Notes"), 
        blank=True,
        help_text=_("Notes visible only to SAFA staff")
    )
    
    # Payment plan
    payment_plan = models.ForeignKey(
        'SAFAPaymentPlan',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text=_("Payment plan if paying in installments")
    )
    
    class Meta:
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        ordering = ['-issue_date', '-created']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['season_config']),
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - R{self.total_amount}"
    
    def save(self, *args, **kwargs):
        # Generate invoice number if not set
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        
        # Calculate VAT and totals
        self.calculate_totals()
        
        # Set due date if not set
        if not self.due_date:
            from datetime import timedelta
            self.due_date = self.issue_date + timedelta(days=self.payment_terms)
        
        # Calculate outstanding amount
        self.outstanding_amount = self.total_amount - self.paid_amount
        
        # Update status based on payment
        self.update_payment_status()
        
        super().save(*args, **kwargs)
    
    def generate_invoice_number(self):
        """Generate unique invoice number using season config"""
        if self.season_config:
            sequence, created = SAFAInvoiceSequence.objects.get_or_create(
                season_config=self.season_config,
                defaults={
                    'prefix': 'SAFA',
                    'current_number': 1,
                    'number_length': 6
                }
            )
            return sequence.get_next_invoice_number()
        else:
            # Fallback method
            import random
            import string
            while True:
                number = ''.join(random.choices(string.digits, k=8))
                if not Invoice.objects.filter(invoice_number=number).exists():
                    return f"SAFA{number}"
    
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
    
    def add_payment(self, amount, payment_method='', payment_reference=''):
        """Add a payment to this invoice"""
        amount = Decimal(str(amount))
        
        # Create payment record
        payment = InvoicePayment.objects.create(
            invoice=self,
            amount=amount,
            payment_method=payment_method,
            payment_reference=payment_reference,
            payment_date=timezone.now()
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
        if self.player:
            self.player.is_approved = True
            self.player.status = 'ACTIVE'
            self.player.save()
        elif self.official:
            self.official.is_approved = True
            self.official.status = 'ACTIVE'
            self.official.save()
    
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


class InvoiceItem(models.Model):
    """Individual line items for invoices"""
    invoice = models.ForeignKey(
        Invoice, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    
    description = models.CharField(_("Description"), max_length=500)
    quantity = models.DecimalField(
        _("Quantity"), 
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('1.00')
    )
    unit_price = models.DecimalField(
        _("Unit Price (Excl. VAT)"), 
        max_digits=10, 
        decimal_places=2
    )
    line_total = models.DecimalField(
        _("Line Total (Excl. VAT)"), 
        max_digits=12, 
        decimal_places=2,
        blank=True
    )
    
    # Pro-rata information
    is_pro_rata = models.BooleanField(_("Pro-rata Item"), default=False)
    original_amount = models.DecimalField(
        _("Original Annual Amount"), 
        max_digits=10, 
        decimal_places=2,
        null=True, blank=True,
        help_text=_("Original annual amount before pro-rata calculation")
    )
    pro_rata_period = models.CharField(
        _("Pro-rata Period"), 
        max_length=100, 
        blank=True,
        help_text=_("Description of pro-rata period (e.g., '8 months')")
    )
    
    class Meta:
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.description} - R{self.line_total}"
    
    def save(self, *args, **kwargs):
        # Calculate line total
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        
        # Update invoice totals
        self.invoice.subtotal = self.invoice.items.aggregate(
            total=models.Sum('line_total')
        )['total'] or Decimal('0.00')
        self.invoice.save()


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
    
    PAYMENT_STATUS = [
        ('PENDING', _('Pending')),
        ('CONFIRMED', _('Confirmed')),
        ('FAILED', _('Failed')),
        ('REVERSED', _('Reversed')),
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
    
    status = models.CharField(
        _("Payment Status"), 
        max_length=20, 
        choices=PAYMENT_STATUS, 
        default='CONFIRMED'
    )
    
    # Bank details
    bank_name = models.CharField(_("Bank Name"), max_length=100, blank=True)
    branch_code = models.CharField(_("Branch Code"), max_length=20, blank=True)
    account_number = models.CharField(_("Account Number"), max_length=50, blank=True)
    
    # Processing details
    processed_by = models.ForeignKey(
        'accounts.CustomUser',
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


class InvoiceInstallment(TimeStampedModel):
    """Installment schedule for payment plans"""
    invoice = models.ForeignKey(
        Invoice, 
        on_delete=models.CASCADE, 
        related_name='installments'
    )
    
    installment_number = models.PositiveIntegerField(_("Installment Number"))
    due_date = models.DateField(_("Due Date"))
    amount = models.DecimalField(
        _("Installment Amount"), 
        max_digits=12, 
        decimal_places=2
    )
    
    paid_amount = models.DecimalField(
        _("Paid Amount"), 
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    
    status = models.CharField(
        _("Status"), 
        max_length=20, 
        choices=[
            ('PENDING', _('Pending')),
            ('PAID', _('Paid')),
            ('OVERDUE', _('Overdue')),
            ('CANCELLED', _('Cancelled')),
        ],
        default='PENDING'
    )
    
    payment_date = models.DateTimeField(_("Payment Date"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Invoice Installment")
        verbose_name_plural = _("Invoice Installments")
        ordering = ['installment_number']
        unique_together = [('invoice', 'installment_number')]
    
    def __str__(self):
        return f"Installment {self.installment_number} - {self.invoice.invoice_number}"
    
    @property
    def is_overdue(self):
        """Check if installment is overdue"""
        return self.status == 'PENDING' and self.due_date < timezone.now().date()


class InvoiceNote(TimeStampedModel):
    """Notes and communication history for invoices"""
    NOTE_TYPES = [
        ('GENERAL', _('General Note')),
        ('PAYMENT', _('Payment Related')),
        ('DISPUTE', _('Dispute')),
        ('REMINDER', _('Payment Reminder')),
        ('ADJUSTMENT', _('Adjustment')),
        ('SYSTEM', _('System Generated')),
    ]
    
    invoice = models.ForeignKey(
        Invoice, 
        on_delete=models.CASCADE, 
        related_name='notes'
    )
    
    note_type = models.CharField(
        _("Note Type"), 
        max_length=20, 
        choices=NOTE_TYPES, 
        default='GENERAL'
    )
    
    subject = models.CharField(_("Subject"), max_length=200, blank=True)
    content = models.TextField(_("Content"))
    
    is_internal = models.BooleanField(
        _("Internal Note"), 
        default=False,
        help_text=_("Internal notes are only visible to SAFA staff")
    )
    
    created_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    
    class Meta:
        verbose_name = _("Invoice Note")
        verbose_name_plural = _("Invoice Notes")
        ordering = ['-created']
    
    def __str__(self):
        return f"{self.get_note_type_display()} - {self.invoice.invoice_number}"


class InvoiceDocument(TimeStampedModel):
    """Supporting documents for invoices"""
    DOCUMENT_TYPES = [
        ('INVOICE', _('Invoice Document')),
        ('RECEIPT', _('Payment Receipt')),
        ('STATEMENT', _('Account Statement')),
        ('PROOF_OF_PAYMENT', _('Proof of Payment')),
        ('TAX_INVOICE', _('Tax Invoice')),
        ('CREDIT_NOTE', _('Credit Note')),
        ('OTHER', _('Other Document')),
    ]
    
    invoice = models.ForeignKey(
        Invoice, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    
    document_type = models.CharField(
        _("Document Type"), 
        max_length=20, 
        choices=DOCUMENT_TYPES
    )
    
    title = models.CharField(_("Document Title"), max_length=200)
    document_file = models.FileField(
        _("Document File"), 
        upload_to='invoice_documents/',
        help_text=_("Upload PDF, image, or other document file")
    )
    
    file_size = models.PositiveIntegerField(
        _("File Size (bytes)"), 
        null=True, blank=True
    )
    
    uploaded_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    
    class Meta:
        verbose_name = _("Invoice Document")
        verbose_name_plural = _("Invoice Documents")
        ordering = ['-created']
    
    def __str__(self):
        return f"{self.title} - {self.invoice.invoice_number}"
    
    def save(self, *args, **kwargs):
        if self.document_file:
            self.file_size = self.document_file.size
        super().save(*args, **kwargs)


# Import references for the config models
from .config_models import SAFASeasonConfig, SAFAFeeStructure, SAFAPaymentPlan, SAFAInvoiceSequence