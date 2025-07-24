from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from model_utils.models import TimeStampedModel
from django.conf import settings
from django.utils.crypto import get_random_string
import os
from geography.models import (
    ModelWithLogo,
    Province,
    Region,
    LocalFootballAssociation,
    Club as GeographyClub  # Import Club from geography with an alias
)
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid
from decimal import Decimal


# Import utils functions conditionally to avoid import issues
try:
    from utils.qr_code_utils import generate_qr_code, get_member_qr_data
except ImportError:
    # Define dummy functions if utils are not available
    def generate_qr_code(data, size=200):
        return None
    def get_member_qr_data(member):
        return {}

# Constants for default images
DEFAULT_PROFILE_PICTURE = 'default_profile.png'
DEFAULT_LOGO = 'default_logo.png'

# Use the Club from geography instead of duplicating it
# This class should be removed since we're using Club from geography
# class Club(TimeStampedModel, ModelWithLogo):
#     ...

class Member(TimeStampedModel):
    MEMBER_TYPES = [
        ('JUNIOR', 'Junior Member (Under 18)'),
        ('SENIOR', 'Senior Member (18+)'),
        ('OFFICIAL', 'Club Official'),
        ('ADMIN', 'Administrator'),
    ]

    MEMBERSHIP_STATUS = [
        ('PENDING', 'Pending'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
        ('REJECTED', 'Rejected'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='member_profile', null=True,
                              blank=True,
                              help_text=_("The user account associated with this member profile"))

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    # Identification Fields
    safa_id = models.CharField(_("SAFA ID"), max_length=5, unique=True,
                             blank=True, null=True,
                             help_text=_("5-digit unique SAFA identification number"))
    fifa_id = models.CharField(_("FIFA ID"), max_length=7, unique=True,
                             blank=True, null=True,
                             help_text=_("7-digit unique FIFA identification number"))
    id_number = models.CharField(_("ID Number"), max_length=13, blank=True,
                               help_text=_("13-digit South African ID number"))
    passport_number = models.CharField(_('Passport Number'), max_length=25, blank=True, null=True, help_text=_('Passport number for non-citizens'))
    gender = models.CharField(_("Gender"), max_length=1, choices=GENDER_CHOICES,
                            blank=True, help_text=_("Gender as per ID document"))

    # Personal Information
    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100)
    email = models.EmailField(_("Email Address"))
    phone_number = models.CharField(_("Phone Number"), max_length=20, blank=True)
    date_of_birth = models.DateField(_("Date of Birth"))
    member_type = models.CharField(_("Member Type"), max_length=20, choices=MEMBER_TYPES, default='SENIOR', blank=True, null=True)

    # Address Information
    street_address = models.CharField(_("Street Address"), max_length=255, blank=True)
    suburb = models.CharField(_("Suburb"), max_length=100, blank=True)
    city = models.CharField(_("City"), max_length=100, blank=True)
    state = models.CharField(_("State/Province"), max_length=100, blank=True)
    postal_code = models.CharField(_("Postal Code"), max_length=20, blank=True)
    country = models.CharField(_("Country"), max_length=100, blank=True)

    # SAFA Membership Information
    status = models.CharField(
        _("Membership Status"),
        max_length=20,
        choices=MEMBERSHIP_STATUS,
        default='PENDING'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_members'
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True)

    # Registration tracking
    registered_by_admin = models.BooleanField(
        _("Registered by Admin"),
        default=False,
        help_text=_("Whether this member was registered by a club administrator")
    )
    registering_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registered_members',
        help_text=_("The club administrator who registered this member")
    )

    # Geography (for administrative purposes)
    province = models.ForeignKey('geography.Province', on_delete=models.SET_NULL, null=True, blank=True)
    region = models.ForeignKey('geography.Region', on_delete=models.SET_NULL, null=True, blank=True)
    lfa = models.ForeignKey('geography.LocalFootballAssociation', on_delete=models.SET_NULL, null=True, blank=True)
    club = models.ForeignKey(GeographyClub, on_delete=models.SET_NULL, null=True, blank=True, related_name='club_members')
    national_federation = models.ForeignKey(
        'geography.NationalFederation',
        on_delete=models.PROTECT, # Protect from accidental deletion of NationalFederation
        null=False,
        blank=False,
        default=1, # Assuming ID 1 is the default NationalFederation (SAFA)
        help_text=_("The national federation this member belongs to")
    )
    association = models.ForeignKey('geography.Association', on_delete=models.SET_NULL, null=True, blank=True, related_name='associated_members')

    # Images
    profile_picture = models.ImageField(_("Profile Picture"),
                                      upload_to='member_profiles/',
                                      null=True, blank=True)

    # Emergency Contact
    emergency_contact = models.CharField(_("Emergency Contact"),
                                      max_length=100, blank=True)
    emergency_phone = models.CharField(_("Emergency Contact Phone"),
                                    max_length=20, blank=True)
    medical_notes = models.TextField(_("Medical Notes"), blank=True)

    # Document Fields for Player Registration
    id_document_type = models.CharField(
        max_length=2,
        choices=[('ID', 'SA ID'), ('PP', 'Passport')],
        default='ID',
        help_text=_('Type of identification document (SA ID or Passport)')
    )
    id_document = models.FileField(
        upload_to='documents/member_documents/',
        null=True,
        blank=True,
        help_text=_('Upload a scan/photo of the ID or passport')
    )

    # Track if a South African citizen also has a valid SA passport
    has_sa_passport = models.BooleanField(
        _('Has SA Passport'),
        default=False,
        help_text=_('Whether the SA citizen member also has a valid SA passport for international travel')
    )

    # Store the SA passport number for local citizens who have passports
    sa_passport_number = models.CharField(
        _('SA Passport Number'),
        max_length=25,
        blank=True,
        null=True,
        help_text=_('South African passport number for citizens (for international travel)')
    )

    # SA passport document
    sa_passport_document = models.FileField(
        _('SA Passport Document'),
        upload_to='sa_passport_documents/',
        blank=True,
        null=True,
        help_text=_('Upload a copy of the SA passport')
    )

    # SA passport expiry date
    sa_passport_expiry_date = models.DateField(
        _('SA Passport Expiry Date'),
        blank=True,
        null=True,
        help_text=_('Expiry date of the South African passport')
    )

    class Meta:
        verbose_name = _("Member")
        verbose_name_plural = _("Members")
        ordering = ['-created']
        permissions = [
            ("can_manage_club_members", "Can manage club members"),
            ("can_view_club_members", "Can view club members"),
            ("can_initiate_transfer", "Can initiate player transfers"),
            ("can_approve_transfer", "Can approve player transfers"),
            ("can_reject_transfer", "Can reject player transfers"),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_address_display(self):
        """Returns formatted full address"""
        address_parts = [
            self.street_address,
            self.suburb,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ", ".join(part for part in address_parts if part)

    @property
    def profile_picture_url(self):
        """Returns URL for profile picture or default image"""
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return os.path.join(settings.STATIC_URL, DEFAULT_PROFILE_PICTURE)

    @property
    def logo_url(self):
        """Return default logo URL"""
        return os.path.join(settings.STATIC_URL, DEFAULT_LOGO)

    def clean(self):
        super().clean()
        # Validate ID number if provided
        if self.id_number:
            self._validate_id_number()

        # Auto-detect member type based on age if not set
        if self.date_of_birth and not self.member_type:
            age = (timezone.now().date() - self.date_of_birth).days // 365
            self.member_type = 'JUNIOR' if age < 18 else 'SENIOR'

    def save(self, *args, **kwargs):
        # Auto-generate SAFA ID
        if not self.safa_id:
            self.generate_safa_id()

        # Validate before saving
        self.clean()

        super().save(*args, **kwargs)

    def approve_membership(self, approved_by):
        """Approve the member's SAFA registration"""
        self.status = 'ACTIVE'
        self.approved_by = approved_by
        self.approved_date = timezone.now()
        self.save()

    def reject_membership(self, rejected_by, reason):
        """Reject the member's SAFA registration"""
        self.status = 'REJECTED'
        self.rejection_reason = reason
        self.save()

    def generate_safa_id(self):
        """Generate a unique 5-character uppercase alphanumeric code"""
        while True:
            code = get_random_string(length=5,
                                   allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            if not Member.objects.filter(safa_id=code).exists():
                self.safa_id = code
                break

    def generate_qr_code(self, size=200):
        """Generate QR code for member identification"""
        qr_data = get_member_qr_data(self)
        return generate_qr_code(qr_data, size)

    @property
    def qr_code(self):
        """Return QR code for member identification"""
        return self.generate_qr_code()

    @property
    def membership_card_ready(self):
        """Check if member is ready for membership card generation"""
        return (
            self.safa_id and
            self.status == 'ACTIVE' and
            self.profile_picture
        )

    def _validate_id_number(self):
        """Validate South African ID number format and content"""
        id_number = self.id_number.strip()

        if not id_number.isdigit() or len(id_number) != 13:
            raise ValidationError(_("ID number must be 13 digits."))

        try:
            # Extract and validate date of birth
            year = id_number[0:2]
            month = id_number[2:4]
            day = id_number[4:6]

            # Determine century (19xx or 20xx)
            current_year = timezone.now().year % 100
            century = '19' if int(year) > current_year else '20'
            full_year = int(century + year)

            # Validate date
            birth_date = timezone.datetime(full_year, int(month), int(day)).date()

            # Update date_of_birth if it doesn't match ID number
            if self.date_of_birth != birth_date:
                self.date_of_birth = birth_date

            # Extract and validate gender
            gender_digit = int(id_number[6:10])
            id_gender = 'M' if gender_digit >= 5000 else 'F'

            # Update gender if it doesn't match ID number
            if self.gender and self.gender != id_gender:
                raise ValidationError(_("ID number gender doesn't match the selected gender."))
            self.gender = id_gender

            # Validate citizenship digit (should be 0 or 1)
            citizenship = int(id_number[10])
            if citizenship not in [0, 1]:
                raise ValidationError(_("ID number citizenship digit must be 0 or 1."))

            # Validate checksum using Luhn algorithm
            digits = [int(d) for d in id_number]
            checksum = 0
            for i in range(len(digits)):
                if i % 2 == 0:
                    checksum += digits[i]
                else:
                    doubled = digits[i] * 2
                    checksum += doubled if doubled < 10 else (doubled - 9)
            if checksum % 10 != 0:
                raise ValidationError(_("ID number checksum is invalid."))
        except Exception as e:
            raise ValidationError(_("Invalid ID number: ") + str(e))

    @property
    def is_junior(self):
        """Check if member is under 18"""
        if self.date_of_birth:
            age = (timezone.now().date() - self.date_of_birth).days // 365
            return age < 18
        return self.member_type == 'JUNIOR'

    @property
    def age(self):
        """Calculate member's age"""
        if self.date_of_birth:
            return (timezone.now().date() - self.date_of_birth).days // 365
        return None

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

class JuniorMember(Member):
    """Junior members require guardian information"""
    guardian_name = models.CharField(_("Guardian Name"), max_length=100)
    guardian_email = models.EmailField(_("Guardian Email"))
    guardian_phone = models.CharField(_("Guardian Phone"), max_length=20)
    school = models.CharField(_("School"), max_length=100, blank=True)
    birth_certificate = models.ImageField(_("Birth Certificate"), upload_to='documents/birth_certificates/', null=True, blank=True)

    class Meta:
        verbose_name = _("Junior Member")
        verbose_name_plural = _("Junior Members")

    def clean(self):
        super().clean()
        # Force member type to be JUNIOR
        self.member_type = 'JUNIOR'

    def convert_to_senior(self):
        """
        Convert a junior member to a senior member when they turn 18.
        This preserves all the member data but removes the junior-specific information.
        """
        if not self.is_junior:
            # Create a new Member instance with the same data
            senior_member = Member.objects.get(pk=self.pk)
            senior_member.member_type = 'SENIOR'
            senior_member.save()

            # Delete the JuniorMember instance but keep the base Member
            JuniorMember.objects.filter(pk=self.pk).delete()

            return senior_member
        return self

    @classmethod
    def check_for_age_transitions(cls):
        """
        Check for junior members who have turned 18 and should be converted to senior members.
        This method can be run as a scheduled task.
        """
        today = timezone.now().date()
        junior_members = cls.objects.all()

        for junior in junior_members:
            if not junior.is_junior:  # They've turned 18
                junior.convert_to_senior()

                # Send notification email about the transition
                try:
                    subject = "SAFA Membership Update - Senior Status"
                    message = f"""
                    Dear {junior.first_name},

                    Congratulations! As you have now turned 18, your SAFA membership has been
                    automatically updated from Junior to Senior status.

                    Your SAFA ID remains: {junior.safa_id}

                    Please log in to update any personal information if needed.

                    Best regards,
                    SAFA Administration
                    """

                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [junior.email],
                        fail_silently=True,
                    )
                except Exception:
                    pass  # Fail silently if email can't be sent


class ClubRegistration(TimeStampedModel):
    """Represents a member's registration with a specific club after SAFA approval"""
    REGISTRATION_STATUS = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
    ]

    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='club_registration')
    club = models.ForeignKey('geography.Club', on_delete=models.CASCADE, related_name='member_registrations')
    registration_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=REGISTRATION_STATUS, default='PENDING')
    position = models.CharField(max_length=50, blank=True)  # Player position for athletes
    jersey_number = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Club Registration")
        verbose_name_plural = _("Club Registrations")
        unique_together = ('member', 'club')

    def __str__(self):
        return f"{self.member.get_full_name()} - {self.club.name}"

    def clean(self):
        super().clean()
        # Ensure member is approved before club registration
        if self.member.status != 'ACTIVE':
            raise ValidationError(_("Only approved SAFA members can register with clubs"))

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
                           related_name='player_registrations')
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
                name='unique_active_registration',
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


class Official(Member):
    """
    Official model represents club or association staff members like referees, secretaries, etc.
    """
    # Add approval field
    is_approved = models.BooleanField(_("Approved"), default=False,
                                     help_text=_("Whether the official has been approved by an admin"))

    # Position in the club or association
    position = models.ForeignKey('accounts.Position', on_delete=models.PROTECT,
                                related_name='officials',
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
        'geography.Association',
        on_delete=models.SET_NULL,
        related_name='primary_officials',
        blank=True,
        null=True,
        help_text=_("Primary association this official belongs to")
    )

    # Link to referee associations (many-to-many)
    associations = models.ManyToManyField(
        'geography.Association',
        related_name='member_officials',
        blank=True,
        help_text=_("Referee or coaching associations this official belongs to"))

    class Meta:
        verbose_name = _("Official")
        verbose_name_plural = _("Officials")

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



class Transfer(TimeStampedModel):
    """Represents a player transfer between clubs"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]

    player = models.ForeignKey('registration.Player', on_delete=models.CASCADE,
                             related_name='transfers')
    from_club = models.ForeignKey(GeographyClub, on_delete=models.CASCADE,  # Use GeographyClub
                                related_name='transfers_out')
    to_club = models.ForeignKey(GeographyClub, on_delete=models.CASCADE,  # Use GeographyClub
                              related_name='transfers_in')

    # Transfer Details
    request_date = models.DateField(_("Request Date"), default=timezone.now)
    effective_date = models.DateField(_("Effective Date"), null=True, blank=True)
    status = models.CharField(_("Status"), max_length=20,
                            choices=STATUS_CHOICES, default='PENDING')
    transfer_fee = models.DecimalField(_("Transfer Fee (ZAR)"), max_digits=10,
                                     decimal_places=2, default=0,
                                     help_text=_("Transfer fee amount in ZAR (South African Rand)"))
    reason = models.TextField(_("Transfer Reason"), blank=True)

    # Approval Details
    approved_by = models.ForeignKey(Member, on_delete=models.SET_NULL,
                                  null=True, blank=True,
                                  related_name='approved_transfers')
    approved_date = models.DateTimeField(_("Approval Date"), null=True, blank=True)
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True)

    class Meta:
        verbose_name = _("Player Transfer")
        verbose_name_plural = _("Player Transfers")
        ordering = ['-request_date']
        permissions = [
            ("can_initiate_transfer", "Can initiate player transfers"),
            ("can_approve_transfer", "Can approve player transfers"),
            ("can_reject_transfer", "Can reject player transfers"),
            ("can_view_transfer", "Can view player transfers"),
        ]

    def __str__(self):
        return f"{self.player.get_full_name()} - {self.from_club.name} to {self.to_club.name}"

    def clean(self):
        super().clean()
        if self.from_club == self.to_club:
            raise ValidationError(_("Cannot transfer player to the same club."))

        # Check player's status
        if self.player.status in ['INACTIVE', 'SUSPENDED']:
            raise ValidationError(_(
                "Player cannot apply for transfer while their membership status is %(status)s."
            ) % {'status': self.player.get_status_display()})

        # Check if player is registered with from_club
        current_registration = apps.get_model('registration', 'PlayerClubRegistration').objects.filter(
            player=self.player,
            club=self.from_club,
            status='ACTIVE'
        ).first()

        if not current_registration:
            raise ValidationError(_("Player is not actively registered with the source club."))

        # Check for pending transfers
        pending_transfer = Transfer.objects.filter(
            player=self.player,
            status='PENDING'
        ).exclude(pk=self.pk).first()

        if pending_transfer:
            raise ValidationError(_("Player already has a pending transfer."))

    def approve(self, approved_by):
        """Approve the transfer and update registrations"""
        if self.status != 'PENDING':
            raise ValidationError(_("Only pending transfers can be approved."))

        with transaction.atomic():
            # Deactivate current registration
            apps.get_model('registration', 'PlayerClubRegistration').objects.filter(
                player=self.player,
                club=self.from_club,
                status='ACTIVE'
            ).update(status='TRANSFERRED')

            # Create new registration with to_club
            apps.get_model('registration', 'PlayerClubRegistration').objects.create(
                player=self.player,
                club=self.to_club,
                status='ACTIVE',
                registration_date=timezone.now().date()
            )

            # Update transfer record
            self.status = 'APPROVED'
            self.approved_by = approved_by
            self.approved_date = timezone.now()
            self.effective_date = timezone.now().date()
            self.save()

    def reject(self, rejected_by, reason):
        """Reject the transfer"""
        if self.status != 'PENDING':
            raise ValidationError(_("Only pending transfers can be rejected."))

        self.status = 'REJECTED'
        self.approved_by = rejected_by
        self.approved_date = timezone.now()
        self.rejection_reason = reason
        self.save()

class TransferAppeal(TimeStampedModel):
    """Represents an appeal against a rejected transfer"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('UPHELD', 'Upheld'),
        ('DISMISSED', 'Dismissed'),
        ('WITHDRAWN', 'Withdrawn'),
        ('ESCALATED', 'Escalated to Federation'),
        ('FEDERATION_APPROVED', 'Approved by Federation'),
        ('FEDERATION_REJECTED', 'Rejected by Federation'),
    ]

    transfer = models.OneToOneField(
        Transfer,
        on_delete=models.CASCADE,
        related_name='appeal'
    )
    submitted_by = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='submitted_appeals'
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    appeal_reason = models.TextField(_("Appeal Reason"))
    supporting_document = models.FileField(
        _("Supporting Document"),
        upload_to='transfer_appeals/',
        null=True,
        blank=True
    )
    reviewed_by = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_appeals'
    )
    review_date = models.DateTimeField(_("Review Date"), null=True, blank=True)
    review_notes = models.TextField(_("Review Notes"), blank=True)
    appeal_submission_date = models.DateTimeField(
        _("Appeal Submission Date"),
        default=timezone.now
    )
    federation_reviewer = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='federation_reviewed_appeals'
    )
    federation_review_date = models.DateTimeField(
        _("Federation Review Date"),
        null=True,
        blank=True
    )
    federation_review_notes = models.TextField(
        _("Federation Review Notes"),
        blank=True
    )
    requires_federation_approval = models.BooleanField(
        _("Requires Federation Approval"),
        default=False,
        help_text=_("If true, the appeal must be approved by the National Federation")
    )

    class Meta:
        verbose_name = _("Transfer Appeal")
        verbose_name_plural = _("Transfer Appeals")
        ordering = ['-appeal_submission_date']
        permissions = [
            ("can_review_appeals", "Can review transfer appeals"),
            ("can_submit_appeals", "Can submit transfer appeals"),
            ("can_review_federation_appeals", "Can review federation-level appeals"),
        ]

    def __str__(self):
        return f"Appeal for {self.transfer}"

    def clean(self):
        super().clean()
        # Only rejected transfers can be appealed
        if self.transfer.status != 'REJECTED':
            raise ValidationError(_("Only rejected transfers can be appealed."))

        # Check if appeal already exists
        if (TransferAppeal.objects.filter(transfer=self.transfer)
                                .exclude(pk=self.pk).exists()):
            raise ValidationError(_("An appeal already exists for this transfer."))

    def uphold(self, reviewed_by, notes=''):
        """Uphold the appeal and either approve the transfer or escalate to federation"""
        if self.status != 'PENDING':
            raise ValidationError(_("Only pending appeals can be reviewed."))

        with transaction.atomic():
            if self.requires_federation_approval:
                self.status = 'ESCALATED'
                self.reviewed_by = reviewed_by
                self.review_date = timezone.now()
                self.review_notes = notes
                self.save()
            else:
                self.status = 'UPHELD'
                self.reviewed_by = reviewed_by
                self.review_date = timezone.now()
                self.review_notes = notes
                self.save()
                # Approve the transfer
                self.transfer.approve(reviewed_by)

    def federation_review(self, federation_reviewer, approved, notes=''):
        """Review the appeal at federation level"""
        if self.status != 'ESCALATED':
            raise ValidationError(_("Only escalated appeals can be reviewed by federation."))

        with transaction.atomic():
            if approved:
                self.status = 'FEDERATION_APPROVED'
                # Approve the transfer
                self.transfer.approve(federation_reviewer)
            else:
                self.status = 'FEDERATION_REJECTED'

            self.federation_reviewer = federation_reviewer
            self.federation_review_date = timezone.now()
            self.federation_review_notes = notes
            self.save()

# Use this Membership model and remove the duplicate from accounts/models.py
class Membership(models.Model):
    member = models.ForeignKey('Member', on_delete=models.CASCADE)
    club = models.ForeignKey(GeographyClub, on_delete=models.CASCADE)  # Use GeographyClub
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', _('Active')),
            ('INACTIVE', _('Inactive')),
            ('SUSPENDED', _('Suspended')),
        ],
        default='ACTIVE'
    )

    class Meta:
        verbose_name = _('Membership')
        verbose_name_plural = _('Memberships')

    def __str__(self):
        return f"{self.member} - {self.club}"

# Add SAFA ID to clubs in the GeographyClub model (if not already there)
# This should be done in geography/models.py, but we'll add a proxy model here for now
class ClubWithSafaID(GeographyClub):
    """
    Add SAFA ID functionality to clubs from geography app.

    This is a proxy model that extends the Club model from geography app
    to add SAFA ID and QR code functionality without modifying the original model's DB table.
    """
    class Meta:
        proxy = True
        verbose_name = _("Club with SAFA ID")
        verbose_name_plural = _("Clubs with SAFA ID")

    def generate_safa_id(self):
        """Generate a unique 5-character uppercase alphanumeric code for club"""
        if not self.safa_id:
            while True:
                code = get_random_string(length=5,
                                      allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                if not GeographyClub.objects.filter(safa_id=code).exists():
                    self.safa_id = code
                    break
            self.save(update_fields=['safa_id'])
        return self.safa_id

    def generate_qr_code(self, size=200):
        """Generate QR code for club identification"""
        from utils.qr_code_utils import generate_qr_code, get_club_qr_data
        qr_data = get_club_qr_data(self)
        return generate_qr_code(qr_data, size)

    @property
    def qr_code(self):
        """Return QR code for club identification"""
        return self.generate_qr_code()

    # The class methods are no longer needed as instance methods now handle this
    # but we'll keep them for backward compatibility
    @classmethod
    def generate_safa_id_for_club(cls, club):
        """Generate a SAFA ID for any club instance"""
        if isinstance(club, GeographyClub):
            # Convert to proxy model if needed
            if not isinstance(club, cls):
                club = cls.objects.get(pk=club.pk)
            return club.generate_safa_id()
        return None

    @classmethod
    def generate_qr_code_for_club(cls, club, size=200):
        """Generate QR code for any club instance"""
        if isinstance(club, GeographyClub):
            # Convert to proxy model if needed
            if not isinstance(club, cls):
                club = cls.objects.get(pk=club.pk)
            return club.generate_qr_code(size)
        return None


class Vendor(TimeStampedModel):
    """Vendor model for suppliers, merchandise, etc."""
    name = models.CharField(_("Vendor Name"), max_length=200)
    email = models.EmailField(_("Email"), blank=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    address = models.TextField(_("Address"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    logo = models.ImageField(_("Logo"), upload_to='vendor_logos/', blank=True, null=True)
    
    class Meta:
        verbose_name = _("Vendor")
        verbose_name_plural = _("Vendors")
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Invoice(TimeStampedModel):
    """Invoice model for all billing in the system"""
    INVOICE_STATUS = [
        ('PENDING', _('Pending')),
        ('PAID', _('Paid')),
        ('OVERDUE', _('Overdue')),
        ('CANCELLED', _('Cancelled')),
    ]
    
    INVOICE_TYPES = [
        ('REGISTRATION', _('Player Registration')),
        ('MEMBERSHIP', _('Membership Fee')),
        ('EVENT', _('Event Ticket')),
        ('MERCHANDISE', _('Merchandise Order')),
        ('OTHER', _('Other')),
    ]
    
    # Unique identifiers
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invoice_number = models.CharField(_("Invoice Number"), max_length=50, unique=True, blank=True)
    
    # Basic invoice info
    status = models.CharField(_("Status"), max_length=20, choices=INVOICE_STATUS, default='PENDING')
    invoice_type = models.CharField(_("Invoice Type"), max_length=20, choices=INVOICE_TYPES, default='OTHER')
    
    # Relationships
    player = models.ForeignKey(
        'membership.Member',
        on_delete=models.CASCADE,
        related_name='player_invoices',
        null=True, blank=True,
        help_text=_("Player this invoice is for (if player registration)")
    )
    club = models.ForeignKey(
        'geography.Club',
        on_delete=models.CASCADE,
        related_name='invoices',
        null=True, blank=True
    )
    official = models.ForeignKey(
        'registration.Official',
        on_delete=models.CASCADE,
        related_name='official_invoices',
        null=True, blank=True,
        help_text=_("Official this invoice is for (if official registration)")
    )
    association = models.ForeignKey(
        'geography.Association',
        on_delete=models.CASCADE,
        related_name='invoices',
        null=True, blank=True,
        help_text=_("Association this invoice is for (e.g., LFA, Region)")
    )
    vendor = models.ForeignKey(
        'Vendor',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text=_("Vendor associated with this invoice (if applicable)")
    )
    issued_by = models.ForeignKey(
        'membership.Member',
        on_delete=models.SET_NULL,
        related_name='issued_invoices',
        null=True, blank=True
    )
    
    # Generic foreign key for flexible relationships
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Financial details
    amount = models.DecimalField(_("Total Amount"), max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(_("Amount Paid"), max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=10, decimal_places=2, default=0)
    
    # Dates
    issue_date = models.DateField(_("Issue Date"), default=timezone.now)
    due_date = models.DateField(_("Due Date"))
    payment_date = models.DateTimeField(_("Payment Date"), null=True, blank=True)
    
    # Payment details
    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True)
    payment_reference = models.CharField(_("Payment Reference"), max_length=100, blank=True, help_text="Reference number for the payment")
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"INV-{self.invoice_number} - R{self.amount}"
    
    def recalculate_totals(self):
        """
        Recalculates the invoice's amount and tax_amount from its line items.
        Assumes that the unit_price on InvoiceItem is VAT-inclusive.
        """
        items = self.items.all()
        total_incl_vat = sum(item.sub_total for item in items)
        vat_rate = Decimal('1.15')

        if total_incl_vat > 0:
            base_amount = (total_incl_vat / vat_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            tax_amount = total_incl_vat - base_amount
        else:
            base_amount = Decimal('0.00')
            tax_amount = Decimal('0.00')

        # Update the invoice fields without triggering a recursive save signal
        Invoice.objects.filter(pk=self.pk).update(
            amount=base_amount,
            tax_amount=tax_amount
        )

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        if not self.due_date:
            # Default due date is 30 days from issue
            from datetime import timedelta
            self.due_date = self.issue_date + timedelta(days=30)
        super().save(*args, **kwargs)

    def generate_invoice_number(self):
        """Generate unique invoice number"""
        import random
        import string
        while True:
            number = ''.join(random.choices(string.digits, k=8))
            if not Invoice.objects.filter(invoice_number=number).exists():
                return number

    @property
    def is_paid(self):
        return self.status == 'PAID' or self.paid_amount >= self.amount

    @property
    def outstanding_amount(self):
        return self.amount - self.paid_amount

    @property
    def is_overdue(self):
        return self.status == 'OVERDUE' or (
            self.status == 'PENDING' and self.due_date < timezone.now().date()
        )

    @property
    def total_amount(self):
        return self.items.aggregate(total=models.Sum('unit_price'))['total'] or Decimal('0.00')

    def mark_as_paid(self):
        """Marks the invoice as paid and sets the payment date."""
        if self.status != 'PAID':
            self.status = 'PAID'
            self.payment_date = timezone.now()
            self.save(update_fields=['status', 'payment_date'])

class InvoiceItem(models.Model):
    """Individual line items for invoices"""
    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='items')
    description = models.CharField(_("Description"), max_length=200)
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=8, decimal_places=2)
    
    class Meta:
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")
    
    def __str__(self):
        return f"{self.description} (x{self.quantity})"
    
    @property
    def sub_total(self):
        quantity = self.quantity if self.quantity is not None else 0
        unit_price = self.unit_price if self.unit_price is not None else Decimal('0.00')
        return quantity * unit_price

class MembershipApplication(models.Model):
    member = models.ForeignKey('Member', on_delete=models.CASCADE, related_name='applications', null=True, blank=True)
    club = models.ForeignKey(GeographyClub, on_delete=models.CASCADE, related_name='membership_applications')
    signature = models.ImageField(upload_to='signatures/')
    date_signed = models.DateField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_applications')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Application: {self.member} to {self.club} ({self.status})"
