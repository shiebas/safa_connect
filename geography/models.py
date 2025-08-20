# geography/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from utils.models import ModelWithLogo, SAFAIdentifiableMixin  # Import from your utils app instead
from utils.qr_code_utils import generate_qr_code, get_club_qr_data

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

class ClubStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', _('Active')
    INACTIVE = 'INACTIVE', _('Inactive')
    SUSPENDED = 'SUSPENDED', _('Suspended')
    DISSOLVED = 'DISSOLVED', _('Dissolved')

# ===== BASE MODELS =====



class RegistrationType(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g. "Junior Competition", "Public Fan"
    allowed_user_roles = models.CharField(max_length=100)  # Comma-separated roles, e.g. "PLAYER,COACH"

    def __str__(self):
        return self.name

    def get_model_name(self):
        return "Club"

# ===== HIERARCHICAL SPORTS ORGANIZATION MODELS =====

class WorldSportsBody(TimeStampedModel, ModelWithLogo):
    """Represents global governing bodies like FIFA, World Rugby, etc."""
    name = models.CharField(_('Name'), max_length=100)
    acronym = models.CharField(_('Acronym'), max_length=10, blank=True)
    website = models.URLField(_('Website'), max_length=200, blank=True)
    headquarters = models.CharField(_('Headquarters'), max_length=100, blank=True)
    description = models.TextField(_('Description'), blank=True)
    sport_code = models.CharField(
        max_length=10,
        choices=SPORT_CODES,
        blank=True,
        null=True,
        help_text=_("Sport code for this world sports body")
    )
    
    class Meta:
        verbose_name = _('World Sports Body')
        verbose_name_plural = _('World Sports Bodies')
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Continent(TimeStampedModel, ModelWithLogo):
    """Represents the six continents as geographical entities"""
    name = models.CharField(_('Name'), max_length=100)
    code = models.CharField(_('Code'), max_length=2, blank=True)
    world_sports_body = models.ForeignKey(
        WorldSportsBody,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='continents'
    )

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
    """Represents regions within a continent (e.g., Southern Africa within Africa)"""
    name = models.CharField(_('Name'), max_length=100)
    code = models.CharField(_('Code'), max_length=10, blank=True, null=True)
    continent = models.ForeignKey(
        Continent, 
        on_delete=models.CASCADE,
        related_name='regions',
        null=True
    )
    continent_federation = models.ForeignKey(
        ContinentFederation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='regions'
    )
    description = models.TextField(_('Description'), blank=True)
    
    class Meta:
        verbose_name = _('Continent Region')
        verbose_name_plural = _('Continent Regions')
        ordering = ['continent', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.continent.name})"

class Country(TimeStampedModel, ModelWithLogo):
    """Represents a country (e.g., South Africa)"""
    name = models.CharField(_('Name'), max_length=100)
    code = models.CharField(_('Country Code'), max_length=3, blank=True, null=True)
    description = models.TextField(_('Description'), blank=True)
    continent_region = models.ForeignKey(
        ContinentRegion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='countries'
    )
    
    class Meta:
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
class MotherBody(models.Model):
    name = models.CharField(max_length=100, unique=True)
    country = models.ForeignKey(
        'geography.Country',
        on_delete=models.CASCADE,
        help_text="The country this mother body belongs to"
    )

    def __str__(self):
        return self.name    

class NationalFederation(TimeStampedModel, ModelWithLogo, SAFAIdentifiableMixin):
    """Represents a national football federation (e.g., SAFA)"""
    name = models.CharField(_('Name'), max_length=100)
    acronym = models.CharField(_('Acronym'), max_length=10, blank=True)
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE
    )
    website = models.URLField(_('Website'), max_length=200, blank=True)
    headquarters = models.CharField(_('Headquarters'), max_length=100, blank=True)
    description = models.TextField(_('Description'), blank=True)
    
    class Meta:
        verbose_name = _('National Federation')
        verbose_name_plural = _('National Federations')
        ordering = ['country', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.country.name})"

class Province(TimeStampedModel, ModelWithLogo):
    """Represents a province/state within a national federation (e.g., Western Cape)"""
    name = models.CharField(_('Name'), max_length=100, unique=True, null=True, blank=True)
    code = models.CharField(_('Code'), max_length=10, blank=True)
    national_federation = models.ForeignKey(
        NationalFederation,
        null=True,
        on_delete=models.CASCADE,
        help_text=_('The national federation this province belongs to')
    )
    description = models.TextField(_('Description'), blank=True)
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=ClubStatus.choices,
        default=ClubStatus.INACTIVE
    )
    # Add safa_id field manually without mixin to avoid conflicts
    safa_id = models.CharField(
        _("SAFA ID"),
        max_length=20,
        blank=True,
        null=True,
        help_text=_("Unique SAFA identification")
    )
    
    class Meta:
        verbose_name = _('Province')
        verbose_name_plural = _('Provinces')
        ordering = ['national_federation', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.national_federation.name})"

    def get_model_name(self):
        return "Province"

class Region(TimeStampedModel, ModelWithLogo, SAFAIdentifiableMixin):
    """Represents a region within an association (e.g., Southern Region)"""
    name = models.CharField(_('Name'), max_length=100)
    code = models.CharField(_('Code'), max_length=10, blank=True)
    province = models.ForeignKey(
        Province,
        on_delete=models.CASCADE
    )
    description = models.TextField(_('Description'), blank=True)
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=ClubStatus.choices,
        default=ClubStatus.INACTIVE
    )
    
    class Meta:
        verbose_name = _('Region')
        verbose_name_plural = _('Regions')
        ordering = ['province', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.province.name} - {self.province.national_federation.name})"

    def get_model_name(self):
        return "Region"

class Association(TimeStampedModel, ModelWithLogo, SAFAIdentifiableMixin):
    """Represents a regional football association (e.g., SAFA Cape Town)"""
    name = models.CharField(_('Name'), max_length=100)
    acronym = models.CharField(_('Acronym'), max_length=10, blank=True)
    national_federation = models.ForeignKey(
        NationalFederation,
        on_delete=models.CASCADE
    )
    website = models.URLField(_('Website'), max_length=200, blank=True)
    headquarters = models.CharField(_('Headquarters'), max_length=100, blank=True)
    description = models.TextField(_('Description'), blank=True)
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=ClubStatus.choices,
        default=ClubStatus.INACTIVE
    )
    
    class Meta:
        verbose_name = _('Association')
        verbose_name_plural = _('Associations')
        ordering = ['national_federation', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.national_federation.country.name})"

    def get_model_name(self):
        return "Association"



class LocalFootballAssociation(TimeStampedModel, ModelWithLogo, SAFAIdentifiableMixin):
    """Represents a local football association (e.g., Cape Town LFA)"""
    name = models.CharField(_('Name'), max_length=100)
    acronym = models.CharField(_('Acronym'), max_length=10, blank=True)
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE
    )
    association = models.ForeignKey(
        Association,
        on_delete=models.CASCADE,
        null=True,  # Allow NULL values
        blank=True  # Make field optional in forms
    )
    website = models.URLField(_('Website'), max_length=200, blank=True)
    headquarters = models.CharField(_('Headquarters'), max_length=100, blank=True)
    description = models.TextField(_('Description'), blank=True)
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=ClubStatus.choices,
        default=ClubStatus.INACTIVE
    )
    
    class Meta:
        verbose_name = _('Local Football Association')
        verbose_name_plural = _('Local Football Associations')
        ordering = ['region', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.region.name})"

    def get_model_name(self):
        return "LFA"

class ClubTier(models.TextChoices):
    PREMIER = 'PREMIER', _('Premier')
    FIRST_DIVISION = 'FIRST', _('First Division')
    SECOND_DIVISION = 'SECOND', _('Second Division')
    AMATEUR = 'AMATEUR', _('Amateur')
    YOUTH = 'YOUTH', _('Youth/Development')

class Club(TimeStampedModel, ModelWithLogo, SAFAIdentifiableMixin):
    """Represents a football club"""
    name = models.CharField(_('Name'), max_length=100)
    code = models.CharField(
        _('Club Code'), 
        max_length=10, 
        blank=True,
        help_text=_('Short code/abbreviation for the club')
    )
    province = models.ForeignKey(
        Province,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('Province'),
        related_name='clubs'
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('Region'),
        related_name='clubs'
    )
    localfootballassociation = models.ForeignKey(
        LocalFootballAssociation,
        on_delete=models.CASCADE,
        verbose_name=_('Local Football Association'),
        related_name='clubs'
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=ClubStatus.choices,
        default=ClubStatus.ACTIVE
    )
    founding_date = models.DateField(_('Founding Date'), blank=True, null=True)
    website = models.URLField(_('Website'), max_length=200, blank=True)
    stadium = models.CharField(_('Stadium'), max_length=100, blank=True)
    description = models.TextField(_('Description'), blank=True)
    colors = models.CharField(_('Club Colors'), max_length=100, blank=True)
    safa_id = models.CharField(
        _("SAFA ID"),
        max_length=5,  # Changed from 20 to 5
        unique=True,
        blank=True,
        null=True,
        help_text=_("5-digit unique SAFA identification number")
    )
    fifa_id = models.CharField(max_length=7, unique=True, blank=True, null=True, 
                              help_text="7-digit FIFA alphanumeric code (A-Z, 0-9)")
    # Add payment tracking
    payment_confirmed = models.BooleanField(default=False, 
                                          help_text="Payment confirmed for SAFA registration")
    payment_date = models.DateTimeField(null=True, blank=True)
    registration_fee = models.DecimalField(
        verbose_name=_('Registration Fee'),
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text=_('Registration fee amount in ZAR (South African Rand)')
    )
    CLUB_TYPE_CHOICES = [
        ('AMATEUR', 'Amateur'),
        ('SEMI_PROFESSIONAL', 'Semi Professional'),
        ('PROFESSIONAL', 'Professional'),
    ]
    CLUB_OWNER_TYPE_CHOICES = [
        ('PRIVATE', 'Private'),
        ('NPO', 'NPO'),
        ('CONSTITUTIONAL', 'Constitutional'),
    ]
    club_type = models.CharField(
        max_length=20,
        choices=CLUB_TYPE_CHOICES,
        blank=True,
        null=True,
        verbose_name=_('Club Type'),
        help_text=_('Amateur, Semi Professional, or Professional')
    )
    club_owner_type = models.CharField(
        max_length=20,
        choices=CLUB_OWNER_TYPE_CHOICES,
        blank=True,
        null=True,
        verbose_name=_('Club Owner Type'),
        help_text=_('Private, NPO, or Constitutional')
    )
    club_documents = models.FileField(
        upload_to='documents/club_documents/',
        blank=True,
        null=True,
        verbose_name=_('Club Compliance Documents'),
        help_text=_('Upload constitution or other compliance documents (PDF, DOC, etc)')
    )
    affiliation_fees_paid = models.BooleanField(
        default=False,
        verbose_name=_('Affiliation Fees Paid'),
        help_text=_('Has the club paid its affiliation fees for the season?')
    )
    
    class Meta:
        verbose_name = _('Club')
        verbose_name_plural = _('Clubs')
        ordering = ['province', 'region', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Ensure province and region match LFA"""
        if self.localfootballassociation_id:
            self.region = self.localfootballassociation.region
            self.province = self.localfootballassociation.region.province
        
        # Generate 5-digit random alphanumeric SAFA ID if payment confirmed
        if self.payment_confirmed and not self.safa_id:
            import string
            import random
            
            while True:
                chars = string.ascii_uppercase + string.digits
                safa_id = ''.join(random.choices(chars, k=5))
                
                if not Club.objects.filter(safa_id=safa_id).exists():
                    self.safa_id = safa_id
                    break
        
        # Generate FIFA ID if not set (7-digit alphanumeric)
        # Commented out FIFA ID generation
        # if not self.fifa_id:
        #     import string
        #     import random
        #     chars = string.ascii_uppercase + string.digits
        #     while True:
        #         fifa_id = ''.join(random.choices(chars, k=7))
        #         if not Club.objects.filter(fifa_id=fifa_id).exists():
        #             self.fifa_id = fifa_id
        #             break
        super().save(*args, **kwargs)
    
    def confirm_payment(self, amount=None):
        """Confirm payment and generate SAFA ID if needed"""
        from django.utils import timezone
        
        self.payment_confirmed = True
        self.payment_date = timezone.now()
        if amount:
            self.registration_fee = amount
        
        self.save()  # This will trigger SAFA ID generation
        return self.safa_id
    
    def generate_qr_code(self, size=200):
        """Generate QR code for club identification"""
        qr_data = get_club_qr_data(self)
        return generate_qr_code(qr_data, size)
    
    @property
    def qr_code(self):
        """Return QR code for club identification"""
        return self.generate_qr_code()
