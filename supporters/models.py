from django.db import models
from accounts.models import CustomUser
from geography.models import Club

class SupporterProfile(models.Model):
    """Extended profile for supporters"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    favorite_club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True)
    membership_type = models.CharField(
        max_length=20,
        choices=[
            ('PREMIUM', 'Premium Supporter'),
            ('VIP', 'VIP Supporter'),
            ('FAMILY_BASIC', 'Family Basic Package'),
            ('FAMILY_PREMIUM', 'Family Premium Package'),
            ('FAMILY_VIP', 'Family VIP Package'),
        ],
        default='PREMIUM'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # ID verification fields
    id_number = models.CharField(max_length=64, blank=True)
    id_document = models.FileField(upload_to='documents/supporter_ids/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True)
    # Geolocation fields
    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True, help_text="Latitude coordinate")
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True, help_text="Longitude coordinate")
    location_city = models.CharField(max_length=100, blank=True, help_text="City from geolocation")
    location_province = models.CharField(max_length=100, blank=True, help_text="Province from geolocation")
    location_country = models.CharField(max_length=100, blank=True, help_text="Country from geolocation")
    location_accuracy = models.FloatField(blank=True, null=True, help_text="Location accuracy in meters")
    location_timestamp = models.DateTimeField(blank=True, null=True, help_text="When location was captured")
    # Card/invoice integration
    digital_card = models.OneToOneField('membership_cards.DigitalCard', on_delete=models.SET_NULL, null=True, blank=True)
    physical_card = models.OneToOneField('membership_cards.PhysicalCard', on_delete=models.SET_NULL, null=True, blank=True)
    invoice = models.OneToOneField('membership.Invoice', on_delete=models.SET_NULL, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.membership_type}"
