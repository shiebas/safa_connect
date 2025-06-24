from django.db import models
from accounts.models import CustomUser
from geography.models import Club


class SupporterPreferences(models.Model):
    """Preferences matrix for targeted marketing and personalized experiences"""
    
    # Ticket & Event Preferences
    discount_tickets = models.BooleanField(default=False, verbose_name="Discount Tickets & Early Bird Offers")
    vip_experiences = models.BooleanField(default=False, verbose_name="VIP Match Experiences")
    international_matches = models.BooleanField(default=False, verbose_name="International Match Notifications")
    local_matches = models.BooleanField(default=False, verbose_name="Local League Match Updates")
    youth_matches = models.BooleanField(default=False, verbose_name="Youth & Development Matches")
    
    # Merchandise & Retail
    official_jerseys = models.BooleanField(default=False, verbose_name="Official SAFA Jerseys & Kit")
    casual_clothing = models.BooleanField(default=False, verbose_name="Casual SAFA Clothing & Accessories")
    limited_editions = models.BooleanField(default=False, verbose_name="Limited Edition Merchandise")
    seasonal_sales = models.BooleanField(default=False, verbose_name="Seasonal Sales & Clearance")
    
    # Travel & Hospitality
    match_travel_packages = models.BooleanField(default=False, verbose_name="Match Travel Packages")
    accommodation_deals = models.BooleanField(default=False, verbose_name="Discounted Accommodation")
    transport_offers = models.BooleanField(default=False, verbose_name="Transport & Flight Deals")
    international_tours = models.BooleanField(default=False, verbose_name="International Tour Packages")
    
    # Digital & Media
    exclusive_content = models.BooleanField(default=False, verbose_name="Exclusive Digital Content")
    player_interviews = models.BooleanField(default=False, verbose_name="Player Interviews & Behind Scenes")
    live_streaming = models.BooleanField(default=False, verbose_name="Live Streaming Access")
    podcasts_videos = models.BooleanField(default=False, verbose_name="SAFA Podcasts & Video Series")
    
    # Community & Events
    community_events = models.BooleanField(default=False, verbose_name="Community Fan Events")
    coaching_clinics = models.BooleanField(default=False, verbose_name="Coaching Clinics & Workshops")
    player_meetups = models.BooleanField(default=False, verbose_name="Player Meet & Greet Events")
    charity_initiatives = models.BooleanField(default=False, verbose_name="SAFA Charity & CSI Initiatives")
    
    # Food & Beverage
    stadium_dining = models.BooleanField(default=False, verbose_name="Stadium Dining Offers")
    partner_restaurant_deals = models.BooleanField(default=False, verbose_name="Partner Restaurant Discounts")
    catering_packages = models.BooleanField(default=False, verbose_name="Match Day Catering Packages")
    
    # Financial Services
    insurance_products = models.BooleanField(default=False, verbose_name="Sports & Travel Insurance")
    banking_offers = models.BooleanField(default=False, verbose_name="SAFA Partner Banking Offers")
    investment_opportunities = models.BooleanField(default=False, verbose_name="Sports Investment Opportunities")
    
    # Communication Preferences
    email_notifications = models.BooleanField(default=True, verbose_name="Email Notifications")
    sms_alerts = models.BooleanField(default=False, verbose_name="SMS Alerts")
    push_notifications = models.BooleanField(default=True, verbose_name="Mobile App Push Notifications")
    whatsapp_updates = models.BooleanField(default=False, verbose_name="WhatsApp Updates")
    
    # Frequency Preferences
    FREQUENCY_CHOICES = [
        ('IMMEDIATE', 'Immediate (as they happen)'),
        ('DAILY', 'Daily digest'),
        ('WEEKLY', 'Weekly summary'),
        ('MONTHLY', 'Monthly newsletter'),
        ('MAJOR_EVENTS', 'Major events only'),
    ]
    communication_frequency = models.CharField(
        max_length=20, 
        choices=FREQUENCY_CHOICES, 
        default='WEEKLY',
        verbose_name="Communication Frequency"
    )
    
    # Special Interests
    youth_development = models.BooleanField(default=False, verbose_name="Youth Development Programs")
    womens_football = models.BooleanField(default=False, verbose_name="Women's Football")
    disability_football = models.BooleanField(default=False, verbose_name="Disability Football")
    referee_programs = models.BooleanField(default=False, verbose_name="Referee Development Programs")
    coaching_development = models.BooleanField(default=False, verbose_name="Coaching Development")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Supporter Preference"
        verbose_name_plural = "Supporter Preferences"
    
    def __str__(self):
        return f"Preferences for {self.supporterprofile.user.get_full_name()}"
    
    @property
    def total_preferences_selected(self):
        """Count how many preferences are selected"""
        fields = [f for f in self._meta.fields if isinstance(f, models.BooleanField)]
        return sum(1 for field in fields if getattr(self, field.name))
    
    @property
    def preference_categories(self):
        """Get preferences grouped by category"""
        return {
            'Tickets & Events': {
                'discount_tickets': self.discount_tickets,
                'vip_experiences': self.vip_experiences,
                'international_matches': self.international_matches,
                'local_matches': self.local_matches,
                'youth_matches': self.youth_matches,
            },
            'Merchandise': {
                'official_jerseys': self.official_jerseys,
                'casual_clothing': self.casual_clothing,
                'limited_editions': self.limited_editions,
                'seasonal_sales': self.seasonal_sales,
            },
            'Travel & Hospitality': {
                'match_travel_packages': self.match_travel_packages,
                'accommodation_deals': self.accommodation_deals,
                'transport_offers': self.transport_offers,
                'international_tours': self.international_tours,
            },
            'Digital & Media': {
                'exclusive_content': self.exclusive_content,
                'player_interviews': self.player_interviews,
                'live_streaming': self.live_streaming,
                'podcasts_videos': self.podcasts_videos,
            },
            'Community': {
                'community_events': self.community_events,
                'coaching_clinics': self.coaching_clinics,
                'player_meetups': self.player_meetups,
                'charity_initiatives': self.charity_initiatives,
            },
        }


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
    
    # Preferences relationship
    preferences = models.OneToOneField(
        SupporterPreferences, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name="Marketing Preferences"
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
    
    def save(self, *args, **kwargs):
        # Create preferences if they don't exist
        if not self.preferences:
            prefs = SupporterPreferences.objects.create()
            self.preferences = prefs
        super().save(*args, **kwargs)
