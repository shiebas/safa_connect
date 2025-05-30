# geography/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

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

class ProvinceType(models.TextChoices):
    INLAND = 'INLAND', _('Inland Province')
    COASTAL = 'COASTAL', _('Coastal Province')

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
    ('CLUB_ADMIN', _('Club Administrator')),
    ('REFEREE', _('Referee')),
    ('FED_ADMIN', _('Federation Admin')),
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
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)

    @cached_property
    def logo_url(self):
        if self.logo and hasattr(self.logo, 'url'):
            return self.logo.url
        return '/static/default_logo.png'

    class Meta:
        abstract = True


class WorldSportsBody(TimeStampedModel, ModelWithLogo):
    """Represents global governing bodies like FIFA, World Rugby, etc."""
    name = models.CharField(max_length=100)
    acronym = models.CharField(max_length=10, unique=True)
    sport_code = models.CharField(max_length=20, choices=SPORT_CODES)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    continents = models.ManyToManyField('Continent', related_name='world_bodies')  # <-- Add this line

    def __str__(self):
        return f"{self.acronym} - {self.get_sport_code_display()}"

    class Meta:
        verbose_name = "World Sports Body"
        verbose_name_plural = "World Sports Bodies"
        ordering = ['sport_code', 'name']

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
    world_body = models.ForeignKey(WorldSportsBody, on_delete=models.PROTECT, related_name='continental_federations')
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    sport_code = models.CharField(
    max_length=10,  # adjust as needed
    choices=SPORT_CODES,
    help_text="Sport code for this continental federation"
    )

    def __str__(self):
        return f"{self.acronym} - {self.continent.name} ({self.get_sport_code_display()})"

    def save(self, *args, **kwargs):
        if self.sport_code:
            # Automatically set world_body based on sport_code
            try:
                # Attempt to fetch the corresponding WorldSportsBody
                self.world_body = WorldSportsBody.objects.get(sport_code=self.sport_code)
            except WorldSportsBody.DoesNotExist:

                if self._meta.get_field('world_body').null:
                    self.world_body = None

                else:

                    pass 
            except WorldSportsBody.MultipleObjectsReturned:

                raise 
        else:
            # If sport_code is not set (e.g., empty or None),
            # and if the world_body field is nullable, ensure it's set to None.
            world_body_field = self._meta.get_field('world_body') # Get field object once
            if world_body_field.null:
                # If world_body can be null, and it's not already None, set it to None.
                # This avoids an unnecessary database update if the value is already correct.
                if self.world_body is not None: # Avoids redundant assignment
                    self.world_body = None
            # else:
                # If world_body is not nullable and sport_code is not set:
                # This implies a potential design inconsistency if the business rule is
                # "if no sport_code, then no world_body".
                # Current behavior: self.world_body is left as is.
                # If self.world_body is None here (and field is non-nullable without a default),
                # super().save() will likely raise an IntegrityError.
                # Consider logging a warning or raising a custom ValidationError
                # if this state represents an invalid model state according to business rules.
                pass # Explicitly note no action if not nullable here.
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Continent Federation"
        verbose_name_plural = "Continent Federations"
        unique_together = [('continent', 'sport_code')]
        ordering = ['continent', 'sport_code']

class ContinentRegion(TimeStampedModel, ModelWithLogo):

    name = models.CharField(max_length=100)
    acronym = models.CharField(max_length=10, unique=True)
    continent_federation = models.ForeignKey(
        'ContinentFederation',
        on_delete=models.PROTECT,
        related_name='regions'
    )
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    # logo is provided by ModelWithLogo

    class Meta:
        verbose_name = "Continent Region"
        verbose_name_plural = "Continent Regions"
        ordering = ['continent_federation', 'name']

    def __str__(self):
        return f"{self.acronym} - {self.continent_federation.name}"

class Country(TimeStampedModel, ModelWithLogo):
    """Core country model with FIFA codes"""
    name = models.CharField(max_length=100, unique=True)
    fifa_code = models.CharField(max_length=3, unique=True)  # ZAF, NAM, LSO
    association_acronym = models.CharField(max_length=15, default='SAFA')
    continent_region = models.ForeignKey(ContinentRegion, on_delete=models.PROTECT, related_name='countries', null=True, blank=True)
    is_default = models.BooleanField(default=False)

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
    province_type = models.CharField(max_length=10, choices=ProvinceType.choices, default=ProvinceType.INLAND)

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

    def __str__(self):
        return f"{self.name}, {self.province.name}"

    class Meta:
        unique_together = ['code', 'province', 'national_federation']

class LocalFootballAssociation(TimeStampedModel, ModelWithLogo):
    """Local Football Association (LFA) that manages clubs within a region"""
    name = models.CharField(max_length=100)
    acronym = models.CharField(max_length=10, blank=True)
    region = models.ForeignKey(Region, on_delete=models.PROTECT)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        if self.acronym:
            return f"{self.acronym} - {self.name} ({self.region.name})"
        return f"{self.name} ({self.region.name})"

    class Meta:
        verbose_name = "Local Football Association"
        verbose_name_plural = "Local Football Associations"

class Association(TimeStampedModel, ModelWithLogo):
    """Special interest associations like Referee Association, Schools Association, etc."""
    name = models.CharField(max_length=100)
    acronym = models.CharField(max_length=10)
    national_federation = models.ForeignKey(NationalFederation, on_delete=models.PROTECT, related_name='associations')
    association_type = models.CharField(max_length=50)  # e.g., "Referee", "Schools", "Coaches"
    description = models.TextField(blank=True)


    def __str__(self):
        return f"{self.acronym} - {self.name}"

    class Meta:
        unique_together = ['acronym', 'national_federation']

class Club(TimeStampedModel, ModelWithLogo):
    """Local sports clubs"""
    name = models.CharField(_('Name'), max_length=100)
    short_name = models.CharField(_('Short Name'), max_length=50, blank=True)
    code = models.CharField(_('Club Code'), max_length=10, unique=True)
    email = models.EmailField(_('Email'), blank=True)
    phone = models.CharField(_('Phone'), max_length=20, blank=True)
    address = models.TextField(_('Address'), blank=True)
    founded_year = models.PositiveIntegerField(_('Founded Year'), null=True, blank=True)
    region = models.ForeignKey(
        'Region',
        on_delete=models.PROTECT,
        related_name='clubs'
    )
    local_football_association = models.ForeignKey(
        'LocalFootballAssociation',
        on_delete=models.PROTECT,
        related_name='clubs'
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('Club')
        verbose_name_plural = _('Clubs')

    def __str__(self):
        return self.name

# ===== USER MODELS =====




