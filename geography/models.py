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

PROVINCE_TYPE_CHOICES = (
    ('INLAND', _('Inland Province')),
    ('COASTAL', _('Coastal Province')),
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
    province_type = models.CharField(max_length=10, choices=PROVINCE_TYPE_CHOICES, default="Inland")

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
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name='local_football_associations')
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
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=20, blank=True)
    province = models.ForeignKey(Province, on_delete=models.PROTECT, related_name='clubs', null=True)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name='clubs', null=True, blank=True)
    local_football_association = models.ForeignKey(LocalFootballAssociation, on_delete=models.PROTECT, related_name='clubs', null=True, blank=True)
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    home_ground = models.CharField(max_length=100, blank=True)
    club_colors = models.CharField(max_length=100, blank=True)
    notes = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # If local_football_association is set but region is not, set region from LFA
        if self.local_football_association and not self.region:
            self.region = self.local_football_association.region
        super().save(*args, **kwargs)

    def __str__(self):
        if self.local_football_association:
            return f"{self.name} ({self.local_football_association.name})"
        elif self.region:
            return f"{self.name} ({self.region.name})"
        return self.name

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

    def clean(self):
        """Validate model fields"""
        super().clean()

        # Validate ID number if provided
        if self.id_number:
            try:
                self._validate_id_number()
            except Exception as e:
                from django.core.exceptions import ValidationError
                raise ValidationError({"id_number": str(e)})

    def save(self, *args, **kwargs):
        """Override save method to validate ID number if it has changed"""
        # Only validate ID number if it has changed
        if self.id_number and (not self.pk or self._meta.model.objects.get(pk=self.pk).id_number != self.id_number):
            try:
                # Only validate the ID number field
                self._validate_id_number()
            except Exception as e:
                # If validation fails, log the error but allow the save to proceed
                # This is a more flexible approach than raising an exception
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"ID number validation failed for user {self.username}: {str(e)}")

        super().save(*args, **kwargs)

    @staticmethod
    def extract_id_info(id_number, country_code='ZAF'):
        """
        Extract and validate information from an ID number based on country.
        Supports South Africa (ZAF/RSA), Namibia (NAM), and Lesotho (LSO).
        Returns a dictionary with date_of_birth, gender, citizenship, and is_valid.
        """
        result = {
            'date_of_birth': None,
            'gender': None,
            'citizenship': None,
            'is_valid': False,
            'error': None
        }

        # Remove any spaces or hyphens
        id_number = id_number.replace(' ', '').replace('-', '')

        # Normalize country code - handle both ZAF and RSA for South Africa
        if country_code == 'RSA':
            country_code = 'ZAF'

        # Validate based on country
        if country_code == 'ZAF':
            # South African ID validation
            # Check if ID number is 13 digits
            if not id_number.isdigit() or len(id_number) != 13:
                result['error'] = "South African ID number must be 13 digits."
                return result

            # Extract date components
            year = id_number[0:2]
            month = id_number[2:4]
            day = id_number[4:6]

            # Validate date
            try:
                # Determine century (19xx or 20xx)
                from django.utils import timezone
                current_year = timezone.now().year % 100
                century = '19' if int(year) > current_year else '20'
                full_year = int(century + year)

                # Check if date is valid
                import datetime
                result['date_of_birth'] = datetime.date(full_year, int(month), int(day))
            except ValueError:
                result['error'] = "ID number contains an invalid date of birth."
                return result

            # Extract gender
            gender_digits = int(id_number[6:10])
            result['gender'] = 'M' if gender_digits >= 5000 else 'F'

            # Extract citizenship
            result['citizenship'] = int(id_number[10])
            if result['citizenship'] not in [0, 1]:
                result['error'] = "ID number citizenship digit (11) must be 0 or 1."
                return result

            # Validate checksum (Luhn algorithm)
            total = 0
            for i in range(len(id_number) - 1):
                digit = int(id_number[i])
                if i % 2 == 0:
                    total += digit
                else:
                    # For odd positions, double the digit and sum the digits of the result
                    doubled = digit * 2
                    total += doubled if doubled < 10 else (doubled - 9)

            check_digit = (10 - (total % 10)) % 10
            if check_digit != int(id_number[-1]):
                result['error'] = f"ID number has an invalid checksum digit. Expected {check_digit}, got {id_number[-1]}."
                return result

        elif country_code == 'NAM':
            # Namibian ID validation
            # Namibian IDs are typically 11 digits: YYMMDD SSSCC
            if not id_number.isdigit() or len(id_number) != 11:
                result['error'] = "Namibian ID number must be 11 digits."
                return result

            # Extract date components
            year = id_number[0:2]
            month = id_number[2:4]
            day = id_number[4:6]

            # Validate date
            try:
                # Determine century (19xx or 20xx)
                from django.utils import timezone
                current_year = timezone.now().year % 100
                century = '19' if int(year) > current_year else '20'
                full_year = int(century + year)

                # Check if date is valid
                import datetime
                result['date_of_birth'] = datetime.date(full_year, int(month), int(day))
            except ValueError:
                result['error'] = "ID number contains an invalid date of birth."
                return result

            # For Namibian IDs, we don't have a standard way to determine gender
            # So we'll leave it as None
            result['gender'] = None

        elif country_code == 'LSO':
            # Lesotho ID validation
            # Lesotho IDs can vary in format, but we'll assume they're 8-10 digits
            if not id_number.isdigit() or len(id_number) < 8 or len(id_number) > 10:
                result['error'] = "Lesotho ID number must be 8-10 digits."
                return result

            # For Lesotho IDs, we don't have a standard way to extract date of birth or gender
            # So we'll leave them as None
            result['date_of_birth'] = None
            result['gender'] = None

        else:
            # Unsupported country
            result['error'] = f"ID validation for country code {country_code} is not supported."
            return result

        # If we got here, the ID number is valid
        result['is_valid'] = True
        return result

    def _validate_id_number(self):
        """Validate ID number format and content"""
        if not self.id_number:
            return

        # Remove any spaces or hyphens
        id_number = self.id_number.replace(' ', '').replace('-', '')

        # Get country code for validation
        country_code = 'ZAF'  # Default to South Africa
        if self.country and hasattr(self.country, 'fifa_code'):
            country_code = self.country.fifa_code

        # Extract and validate ID information
        id_info = self.extract_id_info(id_number, country_code)

        if not id_info['is_valid']:
            from django.core.exceptions import ValidationError
            raise ValidationError(id_info['error'])

        # Set date of birth if not already set and available from ID
        if not self.date_of_birth and id_info['date_of_birth']:
            self.date_of_birth = id_info['date_of_birth']

        # Set gender if not already set and available from ID
        if not self.gender and id_info['gender']:
            self.gender = id_info['gender']
        # Otherwise validate gender matches ID number if available
        elif self.gender and id_info['gender'] and self.gender != id_info['gender']:
            from django.core.exceptions import ValidationError
            raise ValidationError(f"ID number gender doesn't match the selected gender ({self.gender}).")

        # Store the cleaned ID number
        self.id_number = id_number

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

    def generate_qr_code(self, size=200):
        """
        Generate a QR code for the user.
        Returns the QR code as a base64 encoded string that can be embedded in HTML.
        """
        try:
            import qrcode
            import base64
            from io import BytesIO

            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )

            # Data to encode in QR code
            data = {
                'id': str(self.id),
                'username': self.username,
                'name': f"{self.name} {self.surname}",
                'role': self.role,
                'safa_id': self.safa_id or '',
                'fifa_id': self.fifa_id or '',
            }

            # Add data to QR code
            qr.add_data(str(data))
            qr.make(fit=True)

            # Create an image from the QR code
            img = qr.make_image(fill_color="black", back_color="white")

            # Save the image to a BytesIO object
            buffer = BytesIO()
            img.save(buffer)

            # Encode the image as base64
            img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')

            return f"data:image/png;base64,{img_str}"
        except ImportError:
            # If qrcode is not installed, return None
            return None


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
