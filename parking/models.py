from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class ParkingZone(models.Model):
    """Represents a parking zone in the stadium."""
    name = models.CharField(_("Zone Name"), max_length=100, unique=True)
    gps_coordinates = models.CharField(_("GPS Coordinates"), max_length=100, blank=True, help_text="Comma-separated latitude and longitude.")

    def __str__(self):
        return self.name

class ParkingSpace(models.Model):
    """Represents a single parking space."""
    zone = models.ForeignKey(ParkingZone, on_delete=models.CASCADE, related_name='spaces')
    space_number = models.CharField(_("Space Number"), max_length=20)
    is_available = models.BooleanField(_("Is Available"), default=True)
    gps_coordinates = models.CharField(_("GPS Coordinates"), max_length=100, blank=True, help_text="Comma-separated latitude and longitude.")

    class Meta:
        unique_together = ('zone', 'space_number')

    def __str__(self):
        return f"{self.zone.name} - {self.space_number}"

class ParkingAllocation(models.Model):
    """Represents the allocation of a parking space to a user for a specific event."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='parking_allocations')
    space = models.ForeignKey(ParkingSpace, on_delete=models.CASCADE, related_name='allocations')
    event = models.ForeignKey('events.InternationalMatch', on_delete=models.CASCADE, related_name='parking_allocations')
    qr_code = models.CharField(_("QR Code"), max_length=255, blank=True, unique=True)
    is_active = models.BooleanField(_("Is Active"), default=True)

    def __str__(self):
        return f"{self.user} - {self.space} for {self.event}"