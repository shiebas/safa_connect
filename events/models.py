from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from geography.models import Region, Province
from supporters.models import SupporterProfile
from membership.invoice_models import Invoice
import uuid
import string
import random

User = get_user_model()


class Stadium(models.Model):
    """Stadium information for events"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=50, blank=True)
    capacity = models.PositiveIntegerField()
    
    # Location
    city = models.CharField(max_length=100)
    province = models.ForeignKey(Province, on_delete=models.CASCADE)
    address = models.TextField(blank=True)
    
    # Stadium details
    surface_type = models.CharField(
        max_length=20,
        choices=[
            ('GRASS', 'Natural Grass'),
            ('ARTIFICIAL', 'Artificial Turf'),
            ('HYBRID', 'Hybrid'),
        ],
        default='GRASS'
    )
    
    # Facilities
    has_roof = models.BooleanField(default=False)
    has_lighting = models.BooleanField(default=True)
    parking_spaces = models.PositiveIntegerField(default=0)
    
    # Management
    contact_person = models.CharField(max_length=200, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({self.city})"


class SeatMap(models.Model):
    """Individual seats in a stadium"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stadium = models.ForeignKey(Stadium, on_delete=models.CASCADE, related_name='seats')
    
    # Seat identification
    section = models.CharField(max_length=20)  # A, B, C, VIP, etc.
    row = models.CharField(max_length=10)     # 1, 2, A, B, etc.
    seat_number = models.CharField(max_length=10)  # 1, 2, 3, etc.
    
    # Pricing and categories
    price_tier = models.CharField(
        max_length=20,
        choices=[
            ('PREMIUM', 'Premium'),
            ('VIP', 'VIP'),
            ('STANDARD', 'Standard'),
            ('ECONOMY', 'Economy'),
            ('STUDENT', 'Student'),
            ('CORPORATE', 'Corporate Box'),
        ]
    )
    base_price = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Accessibility
    is_wheelchair_accessible = models.BooleanField(default=False)
    has_restricted_view = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['stadium', 'section', 'row', 'seat_number']
        ordering = ['section', 'row', 'seat_number']
        
    def __str__(self):
        return f"{self.stadium.short_name or self.stadium.name} - {self.section}{self.row}-{self.seat_number}"


class InternationalMatch(models.Model):
    """International matches and events"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    safa_id = models.CharField(max_length=20, unique=True, blank=True)
    
    # Match details
    name = models.CharField(max_length=200)  # "SAFA vs Nigeria"
    description = models.TextField(blank=True)
    match_type = models.CharField(
        max_length=20,
        choices=[
            ('FRIENDLY', 'International Friendly'),
            ('QUALIFIER', 'World Cup Qualifier'),
            ('AFCON', 'AFCON Match'),
            ('COSAFA', 'COSAFA Cup'),
            ('TOURNAMENT', 'Tournament Match'),
        ]
    )
    
    # Teams
    home_team = models.CharField(max_length=100, default='South Africa')
    away_team = models.CharField(max_length=100)
    
    # Venue and scheduling
    stadium = models.ForeignKey(Stadium, on_delete=models.CASCADE)
    match_date = models.DateTimeField()
    
    # Ticket sales
    tickets_available = models.PositiveIntegerField(default=0)
    tickets_sold = models.PositiveIntegerField(default=0)
    sales_open_date = models.DateTimeField()
    sales_close_date = models.DateTimeField()
    
    # Pricing
    enable_early_bird = models.BooleanField(default=True)
    early_bird_discount = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    early_bird_end_date = models.DateTimeField(null=True, blank=True)
    
    # Group discounts
    enable_group_discount = models.BooleanField(default=True)
    group_size_minimum = models.PositiveIntegerField(default=10)
    group_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Management
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-match_date']
        
    def __str__(self):
        return f"{self.home_team} vs {self.away_team} - {self.match_date.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        if not self.safa_id:
            # Generate SAFA ID: INTL-YYYY-XXX
            year = self.match_date.year
            count = InternationalMatch.objects.filter(match_date__year=year).count() + 1
            self.safa_id = f"INTL-{year}-{count:03d}"
        super().save(*args, **kwargs)
    
    @property
    def tickets_remaining(self):
        return self.tickets_available - self.tickets_sold
    
    @property
    def is_sold_out(self):
        return self.tickets_sold >= self.tickets_available
    
    @property
    def is_early_bird_active(self):
        if not self.enable_early_bird or not self.early_bird_end_date:
            return False
        return timezone.now() <= self.early_bird_end_date
    
    @property
    def sales_status(self):
        now = timezone.now()
        if now < self.sales_open_date:
            return 'PENDING'
        elif now > self.sales_close_date:
            return 'CLOSED'
        elif self.is_sold_out:
            return 'SOLD_OUT'
        else:
            return 'OPEN'


class Ticket(models.Model):
    """Individual tickets for international matches"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Match and seating
    match = models.ForeignKey(InternationalMatch, on_delete=models.CASCADE, related_name='tickets')
    seat = models.ForeignKey(SeatMap, on_delete=models.CASCADE)
    
    # Buyer information
    supporter = models.ForeignKey(SupporterProfile, on_delete=models.CASCADE, related_name='tickets')
    
    # Pricing
    base_price = models.DecimalField(max_digits=8, decimal_places=2)
    discount_applied = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    final_price = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Payment
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='event_tickets')
    
    # Digital ticket
    qr_code = models.CharField(max_length=100, unique=True, blank=True)
    barcode = models.CharField(max_length=50, unique=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('RESERVED', 'Reserved'),
            ('PAID', 'Paid'),
            ('USED', 'Used'),
            ('CANCELLED', 'Cancelled'),
            ('REFUNDED', 'Refunded'),
        ],
        default='RESERVED'
    )
    
    # Timestamps
    purchased_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    
    # Additional information
    special_requirements = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['match', 'seat']
        ordering = ['-purchased_at']
        
    def __str__(self):
        return f"Ticket {self.ticket_number} - {self.match.name}"
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Generate ticket number: INTL-YYYY-XXXXXXX
            year = self.match.match_date.year
            count = Ticket.objects.filter(match__match_date__year=year).count() + 1
            self.ticket_number = f"INTL-{year}-{count:07d}"
        
        if not self.qr_code:
            # Generate unique QR code
            self.qr_code = f"QR-{self.ticket_number}-{get_random_string(8)}"
        
        if not self.barcode:
            # Generate unique barcode
            self.barcode = f"BC{get_random_string(12, string.digits)}"
        
        super().save(*args, **kwargs)


class TicketGroup(models.Model):
    """Group booking for tickets"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Group details
    match = models.ForeignKey(InternationalMatch, on_delete=models.CASCADE, related_name='ticket_groups')
    primary_contact = models.ForeignKey(SupporterProfile, on_delete=models.CASCADE)
    
    # Group information
    group_name = models.CharField(max_length=200, blank=True)
    group_size = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_applied = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    # Payment
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='ticket_groups')
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('CONFIRMED', 'Confirmed'),
            ('PAID', 'Paid'),
            ('CANCELLED', 'Cancelled'),
        ],
        default='PENDING'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Group {self.group_number} - {self.group_name or 'Unnamed'}"
    
    def save(self, *args, **kwargs):
        if not self.group_number:
            # Generate group number: GRP-YYYY-XXX
            year = self.match.match_date.year
            count = TicketGroup.objects.filter(match__match_date__year=year).count() + 1
            self.group_number = f"GRP-{year}-{count:03d}"
        super().save(*args, **kwargs)


def get_random_string(length, allowed_chars=string.ascii_uppercase + string.digits):
    """Generate a random string of specified length"""
    return ''.join(random.choice(allowed_chars) for _ in range(length))
