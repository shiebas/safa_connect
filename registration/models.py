from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from django.conf import settings
from geography.models import Club as GeographyClub, Association
from accounts.models import Position
from membership.models import Member

class Player(Member):
    """
    Player model represents a registered member who can play for clubs.
    Physical attributes and position details are handled in club registration.
    """
    # Add approval field
    is_approved = models.BooleanField(_("Approved"), default=False,
                                     help_text=_("Whether the player has been approved by an admin"))

    class Meta:
        verbose_name = _("Player")
        verbose_name_plural = _("Players")
        default_related_name = "registration_players"

    def clean(self):
        super().clean()
        # Force role to be PLAYER
        self.role = 'PLAYER'

    def __str__(self):
        return f"{self.get_full_name()} - {self.safa_id or 'No SAFA ID'}"

    def save(self, *args, **kwargs):
        # Force role to be PLAYER before saving
        self.role = 'PLAYER'
        # Synchronize status with is_approved
        if self.is_approved:
            self.status = 'ACTIVE'
        else:
            self.status = 'PENDING'
        super().save(*args, **kwargs)

class Official(Member):
    """
    Official model represents club or association staff members like referees, secretaries, etc.
    """
    # Add approval field
    is_approved = models.BooleanField(_("Approved"), default=False,
                                     help_text=_("Whether the official has been approved by an admin"))

    # Position in the club or association
    position = models.ForeignKey(Position, on_delete=models.PROTECT,
                                related_name='registration_officials',
                                help_text=_("Official's position or role in the club/association"))

    # Certification information
    certification_number = models.CharField(_("Certification Number"), max_length=50, blank=True, null=True,
                                          help_text=_("Certification or license number if applicable"))

    certification_document = models.FileField(_("Certification Document"), upload_to='certification_documents/',
                                           blank=True, null=True,
                                           help_text=_("Upload proof of certification or qualification"))

    certification_expiry_date = models.DateField(_("Certification Expiry Date"), blank=True, null=True,
                                              help_text=_("Expiry date of the certification or license"))

    # For referees
    referee_level = models.CharField(_("Referee Level"), max_length=20, blank=True, null=True,
                                  choices=[
                                      ('LOCAL', 'Local'),
                                      ('REGIONAL', 'Regional'),
                                      ('PROVINCIAL', 'Provincial'),
                                      ('NATIONAL', 'National'),
                                      ('INTERNATIONAL', 'International'),
                                  ],
                                  help_text=_("Level of referee qualification if applicable"))

    # Primary association (foreign key)
    primary_association = models.ForeignKey(
        Association,
        on_delete=models.SET_NULL,
        related_name='registration_primary_officials',
        blank=True,
        null=True,
        help_text=_("Primary association this official belongs to")
    )

    # Link to referee associations (many-to-many)
    associations = models.ManyToManyField(
        Association,
        related_name='member_officials_registration',
        blank=True,
        help_text=_("Referee or coaching associations this official belongs to"))

    class Meta:
        verbose_name = _("Official")
        verbose_name_plural = _("Officials")
        default_related_name = "registration_officials"

    def clean(self):
        super().clean()
        # Force role to be OFFICIAL
        self.role = 'OFFICIAL'

    def __str__(self):
        position_name = self.position.title if self.position else "No Position"
        return f"{self.get_full_name()} - {position_name}"

    def save(self, *args, **kwargs):
        # Force role to be OFFICIAL before saving
        self.role = 'OFFICIAL'

        # Sync associations between CustomUser and Official
        if hasattr(self, 'user') and self.user:
            # If user has an association but official doesn't have a primary, set it
            if self.user.association and not self.primary_association:
                self.primary_association = self.user.association
                print(f"[DEBUG - OFFICIAL SAVE] Setting primary_association from user: {self.user.association}")

            # If official has a primary association but user doesn't have one, set it
            elif self.primary_association and not self.user.association:
                self.user.association = self.primary_association
                self.user.save(update_fields=['association'])
                print(f"[DEBUG - OFFICIAL SAVE] Setting user.association from primary: {self.primary_association}")

        # Now save the official
        super().save(*args, **kwargs)

        # Add primary association to associations M2M if it exists and isn't already there
        if self.primary_association:
            if not self.associations.filter(id=self.primary_association.id).exists():
                self.associations.add(self.primary_association)
                print(f"[DEBUG - OFFICIAL SAVE] Added primary_association to associations M2M")


class OfficialCertification(TimeStampedModel):
    """
    Tracks certification history for officials (referees, coaches, etc.)
    Allows recording multiple certifications with dates obtained
    """
    CERTIFICATION_TYPES = [
        ('REFEREE', _('Referee Certification')),
        ('COACH', _('Coaching Certification')),
        ('ADMIN', _('Administrative Certification')),
        ('OTHER', _('Other Certification')),
    ]

    LEVEL_CHOICES = [
        ('LOCAL', _('Local')),
        ('REGIONAL', _('Regional')),
        ('PROVINCIAL', _('Provincial')),
        ('NATIONAL', _('National')),
        ('INTERNATIONAL', _('International')),
    ]

    official = models.ForeignKey(Official, on_delete=models.CASCADE,
                              related_name='certifications',
                              help_text=_("The official who holds this certification"))

    certification_type = models.CharField(_("Certification Type"), max_length=20,
                                       choices=CERTIFICATION_TYPES,
                                       help_text=_("Type of certification"))

    level = models.CharField(_("Level"), max_length=20,
                          choices=LEVEL_CHOICES,
                          help_text=_("Level or grade of the certification"))

    name = models.CharField(_("Certification Name"), max_length=100,
                         help_text=_("Name of the specific certification or qualification"))

    issuing_body = models.CharField(_("Issuing Organization"), max_length=100,
                                 help_text=_("Organization that issued this certification"))

    certification_number = models.CharField(_("Certification Number"), max_length=50,
                                         blank=True, null=True,
                                         help_text=_("Unique identifier for this certification"))

    obtained_date = models.DateField(_("Date Obtained"),
                                  help_text=_("When the certification was first obtained"))

    expiry_date = models.DateField(_("Expiry Date"),
                                blank=True, null=True,
                                help_text=_("When the certification expires (if applicable)"))

    document = models.FileField(_("Certificate Document"),
                             upload_to='certification_documents/history/',
                             blank=True, null=True,
                             help_text=_("Upload proof of certification"))

    notes = models.TextField(_("Notes"), blank=True,
                          help_text=_("Additional information about this certification"))

    is_verified = models.BooleanField(_("Verified"), default=False,
                                   help_text=_("Whether this certification has been verified by an administrator"))

    class Meta:
        verbose_name = _("Official Certification")
        verbose_name_plural = _("Official Certifications")
        ordering = ['-obtained_date']

    def __str__(self):
        return f"{self.official.get_full_name()} - {self.name} ({self.level})"

    @property
    def is_active(self):
        """Check if certification is currently active based on expiry date"""
        if not self.expiry_date:
            return True  # Certifications without expiry dates are considered active
        return self.expiry_date >= timezone.now().date()

    @property
    def validity_status(self):
        """Return the validity status of the certification"""
        if not self.is_verified:
            return "Pending Verification"
        if not self.expiry_date:
            return "Active (No Expiration)"
        if self.is_active:
            return "Active"
        return "Expired"

class PlayerClubRegistration(TimeStampedModel):
    """Represents a player's registration with a specific club"""
    POSITION_CHOICES = [
        ('GK', 'Goalkeeper'),
        ('DF', 'Defender'),
        ('MF', 'Midfielder'),
        ('FW', 'Forward'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
        ('TRANSFERRED', 'Transferred'),
    ]

    player = models.ForeignKey(Player, on_delete=models.CASCADE,
                             related_name='club_registrations')
    club = models.ForeignKey(GeographyClub, on_delete=models.CASCADE,  # Use GeographyClub
                           related_name='registration_player_registrations')
    # Registration Details
    registration_date = models.DateField(_("Registration Date"), default=timezone.now)
    status = models.CharField(_("Status"), max_length=20,
                            choices=STATUS_CHOICES, default='PENDING')
    expiry_date = models.DateField(_("Registration Expiry"), null=True, blank=True)

    # Playing Details
    position = models.CharField(_("Position"), max_length=2,
                              choices=POSITION_CHOICES, blank=True)
    jersey_number = models.PositiveIntegerField(_("Jersey Number"),
                                              blank=True, null=True)
    # Physical Attributes
    height = models.DecimalField(_("Height (cm)"), max_digits=5,
                               decimal_places=2, blank=True, null=True)
    weight = models.DecimalField(_("Weight (kg)"), max_digits=5,
                               decimal_places=2, blank=True, null=True)

    # Additional Information
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Player Club Registration")
        verbose_name_plural = _("Player Club Registrations")
        ordering = ['-registration_date']
        constraints = [
            models.UniqueConstraint(
                fields=['player', 'club'],
                name='unique_active_registration_registration',
                condition=models.Q(status='INACTIVE')
            )
        ]

    def __str__(self):
        return f"{self.player.get_full_name()} - {self.club.name}"

    def clean(self):
        super().clean()
        # Ensure player doesn't have another active registration
        if self.status == 'ACTIVE':
            existing = PlayerClubRegistration.objects.filter(
                player=self.player,
                status='ACTIVE'
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(_(
                    "Player already has an active registration with another club. "
                    "Please transfer or deactivate the existing registration first."
                ))