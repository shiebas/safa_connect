from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from model_utils.models import TimeStampedModel
import uuid
from membership.models.vendor import Vendor

class Invoice(TimeStampedModel):
    """
    Invoice model to track payments for registrations, transfers, etc.
    """
    INVOICE_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELED', 'Canceled'),
        ('REFUNDED', 'Refunded'),
    ]
    
    INVOICE_TYPE_CHOICES = [
        ('REGISTRATION', 'Registration'),
        ('TRANSFER', 'Transfer'),
        ('RENEWAL', 'Renewal'),
        ('OTHER', 'Other'),
    ]
    
    # Invoice identification
    invoice_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text=_("Unique invoice number")
    )
    
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text=_("Universally unique identifier for public links")
    )
    
    reference = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Payment reference code")
    )
    
    # Invoice categorization
    invoice_type = models.CharField(
        max_length=20,
        choices=INVOICE_TYPE_CHOICES,
        default='REGISTRATION',
    )
    
    # Financial details
    amount = models.DecimalField(
        _("Amount"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Total amount in ZAR")
    )
    
    tax_amount = models.DecimalField(
        _("Tax Amount"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("Tax amount in ZAR")
    )
    
    # Status and dates
    status = models.CharField(
        max_length=20,
        choices=INVOICE_STATUS_CHOICES,
        default='PENDING',
    )
    
    issue_date = models.DateField(
        _("Issue Date"),
        default=timezone.now,
    )
    
    due_date = models.DateField(
        _("Due Date"),
        null=True,
        blank=True,
    )
    
    payment_date = models.DateField(
        _("Payment Date"),
        null=True,
        blank=True,
    )
    
    # Relationships
    player = models.ForeignKey(
        'Player',
        on_delete=models.CASCADE,
        related_name='invoices',
        null=True,
        blank=True,
        help_text=_("Player this invoice is for (if player registration)")
    )
    
    official = models.ForeignKey(
        'Official',
        on_delete=models.CASCADE,
        related_name='invoices',
        null=True,
        blank=True,
        help_text=_("Official this invoice is for (if official registration)")
    )
    
    club = models.ForeignKey(
        'geography.Club',
        on_delete=models.PROTECT,
        related_name='invoices',
    )
    
    issued_by = models.ForeignKey(
        'Member',
        on_delete=models.PROTECT,
        related_name='issued_invoices',
    )
    
    # For relationship with PlayerClubRegistration or Transfer
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    
    # Payment method
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('EFT', 'EFT/Bank Transfer'),
            ('CARD', 'Credit/Debit Card'),
            ('CASH', 'Cash'),
            ('OTHER', 'Other'),
        ],
        default='EFT',
    )
    
    # Additional notes
    notes = models.TextField(
        _("Notes"),
        blank=True,
    )
    
    vendor = models.ForeignKey(
        'membership.Vendor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        help_text=_('Vendor associated with this invoice (if applicable)')
    )
    
    association = models.ForeignKey(
        'geography.Association',
        on_delete=models.PROTECT,
        related_name='invoices',
        null=True,
        blank=True,
    )
    
    class Meta:
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        ordering = ['-issue_date', '-created']
    
    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.player.get_full_name()}"
    
    def save(self, *args, **kwargs):
        # Generate invoice number if not set
        if not self.invoice_number:
            year = timezone.now().year
            # Get count of invoices this year and increment
            count = Invoice.objects.filter(
                invoice_number__startswith=f"INV-{year}-"
            ).count() + 1
            self.invoice_number = f"INV-{year}-{count:06d}"
        
        # Set due date if not set (default to 14 days from issue date)
        if not self.due_date:
            self.due_date = self.issue_date + timezone.timedelta(days=14)
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('membership:invoice_detail', kwargs={'uuid': self.uuid})
    
    @property
    def is_paid(self):
        return self.status == 'PAID'
    
    @property
    def is_overdue(self):
        if self.status != 'PAID' and self.due_date:
            return self.due_date < timezone.now().date()
        return False
    
    def mark_as_paid(self, payment_date=None):
        """
        Mark invoice as paid and set payment date. Activate player and registration if registration invoice.
        """
        self.status = 'PAID'
        self.payment_date = payment_date or timezone.now().date()
        self.save()
        # Workflow automation: activate player and registration if registration invoice
        if self.invoice_type == 'REGISTRATION':
            try:
                registration = self.player.club_registrations.get(club=self.club)
                if registration.status != 'ACTIVE':
                    registration.status = 'ACTIVE'
                    registration.save()
                if self.player.status != 'ACTIVE':
                    self.player.status = 'ACTIVE'
                    self.player.save()
            except Exception:
                pass
    
    def get_payment_instructions(self):
        """
        Return formatted payment instructions
        """
        from ..constants import BANK_DETAILS
        
        instructions = f"""
        Please make payment to the following bank account:
        Bank: {BANK_DETAILS['bank_name']}
        Branch: {BANK_DETAILS['branch_name']} 
        Branch Code: {BANK_DETAILS['Branch_code']}
        Account Type: {BANK_DETAILS['account_type']}
        Account Number: {BANK_DETAILS['account_number']}
        Reference: {self.reference}
        """
        return instructions


class InvoiceItem(models.Model):
    """
    Individual line items for an invoice
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
    )
    
    description = models.CharField(
        _("Description"),
        max_length=255,
    )
    
    quantity = models.PositiveIntegerField(
        _("Quantity"),
        default=1,
    )
    
    unit_price = models.DecimalField(
        _("Unit Price"),
        max_digits=10,
        decimal_places=2,
    )
    
    sub_total = models.DecimalField(
        _("Sub Total"),
        max_digits=10,
        decimal_places=2,
    )
    
    class Meta:
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")
    
    def __str__(self):
        return f"{self.description} - {self.sub_total}"
    
    def save(self, *args, **kwargs):
        # Calculate subtotal
        self.sub_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
