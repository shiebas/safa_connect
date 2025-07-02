# Invoice and Vendor models for SAFA system
# These are essential models that are referenced throughout the system

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from model_utils.models import TimeStampedModel
import uuid
from decimal import Decimal

class Vendor(TimeStampedModel):
    """Vendor model for suppliers, merchandise, etc."""
    name = models.CharField(_("Vendor Name"), max_length=200)
    email = models.EmailField(_("Email"), blank=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    address = models.TextField(_("Address"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    logo = models.ImageField(_("Logo"), upload_to='vendor_logos/', blank=True, null=True)
    
    class Meta:
        verbose_name = _("Vendor")
        verbose_name_plural = _("Vendors")
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Invoice(TimeStampedModel):
    """Invoice model for all billing in the system"""
    INVOICE_STATUS = [
        ('PENDING', _('Pending')),
        ('PAID', _('Paid')),
        ('OVERDUE', _('Overdue')),
        ('CANCELLED', _('Cancelled')),
    ]
    
    INVOICE_TYPES = [
        ('REGISTRATION', _('Player Registration')),
        ('MEMBERSHIP', _('Membership Fee')),
        ('EVENT', _('Event Ticket')),
        ('MERCHANDISE', _('Merchandise Order')),
        ('OTHER', _('Other')),
    ]
    
    # Unique identifiers
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invoice_number = models.CharField(_("Invoice Number"), max_length=50, unique=True, blank=True)
    
    # Basic invoice info
    status = models.CharField(_("Status"), max_length=20, choices=INVOICE_STATUS, default='PENDING')
    invoice_type = models.CharField(_("Invoice Type"), max_length=20, choices=INVOICE_TYPES, default='OTHER')
    
    # Relationships
    player = models.ForeignKey('membership.Member', on_delete=models.CASCADE, 
                              related_name='invoices', null=True, blank=True)
    club = models.ForeignKey('geography.Club', on_delete=models.CASCADE,
                           related_name='invoices', null=True, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    issued_by = models.ForeignKey('membership.Member', on_delete=models.SET_NULL,
                                 related_name='issued_invoices', null=True, blank=True)
    
    # Generic foreign key for flexible relationships
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Financial details
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=10, decimal_places=2, default=0)
    
    # Dates
    issue_date = models.DateField(_("Issue Date"), default=timezone.now)
    due_date = models.DateField(_("Due Date"))
    payment_date = models.DateTimeField(_("Payment Date"), null=True, blank=True)
    
    # Payment details
    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"INV-{self.invoice_number} - R{self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        if not self.due_date:
            # Default due date is 30 days from issue
            from datetime import timedelta
            self.due_date = self.issue_date + timedelta(days=30)
        super().save(*args, **kwargs)
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        import random
        import string
        while True:
            number = ''.join(random.choices(string.digits, k=8))
            if not Invoice.objects.filter(invoice_number=number).exists():
                return number
    
    @property
    def is_paid(self):
        return self.status == 'PAID'
    
    @property
    def is_overdue(self):
        return self.status == 'OVERDUE' or (
            self.status == 'PENDING' and self.due_date < timezone.now().date()
        )
    
    @property
    def total_amount(self):
        return self.amount + self.tax_amount
    
    def mark_as_paid(self):
        """Mark invoice as paid"""
        self.status = 'PAID'
        self.payment_date = timezone.now()
        self.save()
    
    def get_payment_instructions(self):
        """Return payment instructions for this invoice"""
        return f"Please pay R{self.total_amount} for invoice {self.invoice_number}"

class InvoiceItem(models.Model):
    """Individual line items for invoices"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(_("Description"), max_length=200)
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=8, decimal_places=2)
    
    class Meta:
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")
    
    def __str__(self):
        return f"{self.description} (x{self.quantity})"
    
    @property
    def sub_total(self):
        return self.quantity * self.unit_price
