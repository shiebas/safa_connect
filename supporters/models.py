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
            ('FREE', 'Free Supporter'),
            ('PREMIUM', 'Premium Supporter'),
            ('VIP', 'VIP Supporter'),
        ],
        default='FREE'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.membership_type}"
