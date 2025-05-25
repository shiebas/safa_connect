# geography/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.crypto import get_random_string


# ===== CHOICE DEFINITIONS =====
DOCUMENT_TYPES = (
    ('BC', _('Birth Certificate')),
    ('PP', _('Passport')),
    ('ID', _('National ID')),
    ('DL', _('Driver License')),
    ('OT', _('Other')),
)

GENDER_CHOICES = (
    ('M', _('Male')),
    ('F', _('Female')),
)

SPORT_CODES = (
    ('SOCCER', _('Soccer')),
    ('RUGBY', _('Rugby')),
    ('CRICKET', _('Cricket')),
    ('BASKETBALL', _('Basketball')),
    ('HOCKEY', _('Hockey')),
    ('TENNIS', _('Tennis')),
    ('OTHER', _('Other')),
)

WORLD_BODIES = (
    ('FIFA', _('Soccer')),
    ('WR', _('Rugby')),
    ('ICC', _('Cricket')),
    ('FIBA', _('Basketball')),
    ('FIH', _('Hockey')),
    ('ITF', _('Tennis')),
    ('OTHER', _('Other')),
)

ROLES = (
    ('ADMIN', _('System Admin')),
    ('ADMIN_COUNTRY', _('Country Admin')),
    ('PLAYER', _('Player')),
    ('CLUB', _('Club Manager')),
    ('REFEREE', _('Referee')),
    ('FED_ADMIN', _('Federation Admin')),
    ('PUBLIC', _('Public User')),
    ('COACH', _('Coach')),
    ('EXECUTIVE', _('Exco Member')),
)

PLAYER_CATEGORIES = (
    ('JR', _('Junior (<18)')),
    ('SR', _('Senior (18+)')),
    ('SU', _('Supporter')),    
)

CONTINENT = (
    ('AF', _('Africa')),
    ('AS', _('Asia')),
    ('EU', _('Europe')),
    ('NA', _('North America')),
    ('OC', _('Oceania')),
    ('SA', _('South America')),
)

# ===== BASE MODELS =====



class RegistrationType(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g. "Junior Competition", "Public Fan"
    allowed_user_roles = models.CharField(max_length=100)  # Comma-separated roles, e.g. "PLAYER,COACH"

    def __str__(self):
        return self.name

# ===== HIERARCHICAL SPORTS ORGANIZATION MODELS =====


class ModelWithLogo(models.Model):
    # Your existing fields
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    
    @cached_property
    def logo_url(self):
        if self.logo and hasattr(self.logo, 'url'):
            return self.logo.url
        return '/static/images/default_logo.png'  # Path to your default logo
    
    class Meta:
        abstract = True

class WorldSportsBody(TimeStampedModel, ModelWithLogo):
    """Represents global governing bodies like FIFA, World Rugby, etc."""
    name = models.CharField(max_length=100)
    acronym = models.CharField(max_length=10, unique=True)
    sport_code = models.CharField(max_length=20, choices=SPORT_CODES)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='world_bodies_logos/', blank=True, null=True)
    continents = models.ManyToManyField('Continent', related_name='world_bodies')  # <-- Add this line
    
    def __str__(self):
        return f"{self.acronym} - {self.get_sport_code_display()}"
    
    class Meta:
        verbose_name = "World Sports Body"
        verbose_name_plural = "World Sports Bodies"

class Continent(TimeStampedModel):
    """Represents the six continents as geographical entities"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=2, choices=CONTINENT, unique=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        ordering = ['name']

class ContinentFederation(TimeStampedModel, ModelWithLogo):
    """Continental federations like CAF, UEFA, etc."""
    name = models.CharField(max_length=100)
    acronym = models.CharField(max_length=10, unique=True)
    continent = models.ForeignKey(Continent, on_delete=models.PROTECT, related_name='federations')
    world_body = models.ForeignKey(WorldSportsBody, on_delete=models.PROTECT, related_name='continent_federations')
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='continent_federation_logos/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.acronym} - {self.name}"
    
    class Meta:
        verbose_name = "Continental Federation"
        verbose_name_plural = "Continental Federations"
        unique_together = ['continent', 'world_body']

class ContinentRegion(TimeStampedModel, ModelWithLogo):
    """Regional confederations like COSAFA, CECAFA, etc."""
    name = models.CharField(max_length=100)
    acronym = models.CharField(max_length=10, unique=True)
    continent_federation = models.ForeignKey(ContinentFederation, on_delete=models.PROTECT, related_name='regions')
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='continent_region_logos/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.acronym} - {self.name}"
    
    class Meta:
        verbose_name = "Continental Region"
        verbose_name_plural = "Continental Regions"

class Country(TimeStampedModel, ModelWithLogo):
    """Core country model with FIFA codes"""
    name = models.CharField(max_length=100, unique=True)
    fifa_code = models.CharField(max_length=3, unique=True)  # ZAF, NAM, LSO
    association_acronym = models.CharField(max_length=15, default='SAFA')
    continent_region = models.ForeignKey(ContinentRegion, on_delete=models.PROTECT, related_name='countries', null=True, blank=True)
    is_default = models.BooleanField(default=False)
    logo = models.ImageField(upload_to='country_logos/', blank=True, null=True)

    def save(self, *args, **kwargs):
        """Ensure only one default country exists"""
        if self.is_default:
            Country.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.fifa_code})"

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        ordering = ['name']

class NationalFederation(TimeStampedModel, ModelWithLogo):
    """National sports associations like SAFA, USA Soccer, etc."""
    name = models.CharField(max_length=100)
    acronym = models.CharField(max_length=10)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='federations')
    world_body = models.ForeignKey(WorldSportsBody, on_delete=models.PROTECT, related_name='national_federations')
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='national_federation_logos/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.acronym} - {self.country.name}"
    
    class Meta:
        verbose_name = "National Federation"
        verbose_name_plural = "National Federations"
        unique_together = ['country', 'world_body']

class Province(TimeStampedModel, ModelWithLogo):
    """Provinces or states within a country"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=5)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='provinces')
    logo = models.ImageField(upload_to='province_logos/', blank=True, null=True)

    def __str__(self):
        return f"{self.name}, {self.country.name}"
    
    class Meta:
        unique_together = ['code', 'country']

class Region(TimeStampedModel, ModelWithLogo):
    """Regions within provinces/states"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    province = models.ForeignKey(Province, on_delete=models.PROTECT, related_name='regions')
    national_federation = models.ForeignKey(NationalFederation, on_delete=models.PROTECT, related_name='regions')
    logo = models.ImageField(upload_to='region_logos/', blank=True, null=True)

    def __str__(self):
        return f"{self.name}, {self.province.name}"
    
    class Meta:
        unique_together = ['code', 'province', 'national_federation']

class Association(TimeStampedModel, ModelWithLogo):
    """Special interest associations like Referee Association, Schools Association, etc."""
    name = models.CharField(max_length=100)
    acronym = models.CharField(max_length=10)
    national_federation = models.ForeignKey(NationalFederation, on_delete=models.PROTECT, related_name='associations')
    association_type = models.CharField(max_length=50)  # e.g., "Referee", "Schools", "Coaches"
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='association_logos/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.acronym} - {self.name}"
    
    class Meta:
        unique_together = ['acronym', 'national_federation']

class Club(TimeStampedModel, ModelWithLogo):
    """Local sports clubs"""
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=20)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name='clubs')
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    home_ground = models.CharField(max_length=100, blank=True)
    club_colors = models.CharField(max_length=100, blank=True)
    logo = models.ImageField(upload_to='club_logos/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.region.name})"

# ===== USER MODELS =====

class CustomUser(AbstractUser, ModelWithLogo):
    registration_type = models.ForeignKey(
        RegistrationType,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    # Core Fields
    role = models.CharField(max_length=20, choices=ROLES, default='PLAYER')
    name = models.CharField(max_length=50, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    surname = models.CharField(max_length=100, blank=True)
    alias = models.CharField(max_length=100, blank=True)
    email = models.EmailField(_('email address'), blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True) # extract from id_number
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='users',
        verbose_name="Registered Country"
    )
    
    # Identification
    id_number = models.CharField(max_length=20, blank=True) # to validate with function
    id_number_other = models.CharField(max_length=25, blank=True, null=True, unique=True)
    passport_number = models.CharField(max_length=25, blank=True)
    id_document_type = models.CharField(
        max_length=2,
        choices=DOCUMENT_TYPES,
        default='ID'
    )
    is_active = models.BooleanField(default=False)  # overwrite default=True from AbstractUser
    membership_card = models.BooleanField(default=False)
    payment_required = models.BooleanField(default=True)
    
    safa_id = models.CharField(max_length=5, unique=True, blank=True, null=True)
    fifa_id = models.CharField(max_length=7, unique=True, blank=True, null=True)

    # Profile image
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    document = models.FileField(upload_to='documents/%Y/%m/%d/', null=True, blank=True)
    # Registration date
    registration_date = models.DateField(default=timezone.now)


    def __str__(self):
        if self.name and self.surname:
            return f"{self.name} {self.surname}"
        return self.username

    def generate_safa_id(self):
        """Generate a unique 5-character uppercase alphanumeric code"""
        while True:
            code = get_random_string(length=5, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            if not CustomUser.objects.filter(safa_id=code).exists():
                self.safa_id = code
                break
    def fetch_fifa_id_from_api(self, api_key):
        # You would call the external API here
        # Example placeholder
        if not self.fifa_id:
            self.fifa_id = get_random_string(length=7, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            self.save()


class Membership(TimeStampedModel):
    """Represents a membership relationship between a user and an organization"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='memberships')
    # Using generic relations to allow membership in different types of organizations
    membership_type = models.CharField(max_length=50)  # e.g., 'club', 'association', 'federation'
    
    # Optional relationships - only one should be used based on membership_type
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='members', null=True, blank=True)
    association = models.ForeignKey(Association, on_delete=models.CASCADE, related_name='members', null=True, blank=True)
    national_federation = models.ForeignKey(NationalFederation, on_delete=models.CASCADE, related_name='members', null=True, blank=True)
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # For players
    player_category = models.CharField(max_length=2, choices=PLAYER_CATEGORIES, null=True, blank=True)
    jersey_number = models.PositiveSmallIntegerField(null=True, blank=True)
    position = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        org_name = ""
        if self.club:
            org_name = self.club.name
        elif self.association:
            org_name = self.association.name
        elif self.national_federation:
            org_name = self.national_federation.name
            
        return f"{self.user} - {org_name}"
    
    class Meta:
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"
