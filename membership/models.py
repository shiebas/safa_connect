from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from model_utils.models import TimeStampedModel
from django.conf import settings
from django.utils.crypto import get_random_string
from accounts.models import CustomUser  # This is correct - keep importing from accounts
import os
from geography.models import (
    ModelWithLogo, 
    Province, 
    Region, 
    LocalFootballAssociation,
    Club as GeographyClub  # Import Club from geography with an alias
)
from django.apps import apps
import sys

# Add path to utils if needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.qr_code_utils import generate_qr_code, get_member_qr_data

# Constants for default images
DEFAULT_PROFILE_PICTURE = 'default_profile.png'
DEFAULT_LOGO = 'default_logo.png'

# Use the Club from geography instead of duplicating it
# This class should be removed since we're using Club from geography
# class Club(TimeStampedModel, ModelWithLogo):
#     ...

class Member(models.Model):
    # Add created field to replace TimeStampedModel
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    
    MEMBERSHIP_STATUS = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('PENDING', 'Pending'),
        ('SUSPENDED', 'Suspended'),
    ]

    ROLE_CHOICES = [
        ('ADMIN_SYSTEM', 'System Administrator'),
        ('ADMIN_COUNTRY', 'Country Administrator'),
        ('ADMIN_FEDERATION', 'Federation Administrator'),
        ('ADMIN_PROVINCE', 'Provincial Administrator'),
        ('ADMIN_REGION', 'Regional Administrator'),
        ('ADMIN_LOCAL_FED', 'Local Federation Administrator'),
        ('CLUB_ADMIN', 'Club Administrator'),
        ('STAFF', 'Staff Member'),
        ('PLAYER', 'Player'),
        ('COACH', 'Coach'),
        ('OFFICIAL', 'Official'),
        ('SUPPORTER', 'Supporter'),
    ]

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
    gender = models.CharField(_("Gender"), max_length=1, choices=GENDER_CHOICES, 
                            blank=True, help_text=_("Gender as per ID document"))

    # Personal Information
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                              related_name='member_profile', null=True, blank=True)
    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100)
    email = models.EmailField(_("Email Address"), unique=True)
    phone_number = models.CharField(_("Phone Number"), max_length=20)
    date_of_birth = models.DateField(_("Date of Birth"))

    # Address Information
    street_address = models.CharField(_("Street Address"), max_length=255, blank=True)
    suburb = models.CharField(_("Suburb"), max_length=100, blank=True)
    city = models.CharField(_("City"), max_length=100, blank=True)
    state = models.CharField(_("State/Province"), max_length=100, blank=True)
    postal_code = models.CharField(_("Postal Code"), max_length=20, blank=True)
    country = models.CharField(_("Country"), max_length=100, blank=True)

    # Membership Information
    club = models.ForeignKey(
        'geography.Club',
        on_delete=models.PROTECT,
        related_name='club_members',  # Changed from 'members'
        null=True,
        blank=True
    )
    role = models.CharField(_("Role"), max_length=20, choices=ROLE_CHOICES, default='PLAYER')
    status = models.CharField(
        _("Membership Status"),
        max_length=10,
        choices=MEMBERSHIP_STATUS,
        default='PENDING'
    )
    membership_number = models.CharField(
        _("Membership Number"),
        max_length=50,
        unique=True,
        blank=True,
        null=True
    )
    registration_date = models.DateField(_("Registration Date"), default=timezone.now)
    expiry_date = models.DateField(_("Expiry Date"), null=True, blank=True)

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
        # Ensure club admins and staff have a club assigned
        if self.role in ['CLUB_ADMIN', 'STAFF'] and not self.club:
            raise ValidationError(_("Club administrators and staff must be assigned to a club."))
        
        # Validate ID number if provided
        if self.id_number:
            self._validate_id_number()

    def save(self, *args, **kwargs):
        # Generate SAFA ID if not set
        if not self.safa_id:
            self.generate_safa_id()
        
        # Validate and save
        self.clean()
        super().save(*args, **kwargs)

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

    def can_access_club(self, club):
        """Check if member can access a specific club's data based on role and jurisdiction"""
        if self.role in ['ADMIN_SYSTEM', 'ADMIN_COUNTRY']:
            return True  # Full access
        if self.role == 'ADMIN_FEDERATION' and self.club and club.federation == self.club.federation:
            return True
        if self.role == 'ADMIN_PROVINCE' and self.club and club.province == self.club.province:
            return True
        if self.role == 'ADMIN_REGION' and self.club and club.region == self.club.region:
            return True
        if self.role == 'ADMIN_LOCAL_FED' and self.club and club.federation == self.club.federation:
            return True
        if self.role == 'CLUB_ADMIN' and self.club == club:
            return True
        return False

class Player(Member):
    """
    Player model represents a registered member who can play for clubs.
    Physical attributes and position details are handled in club registration.
    """
    class Meta:
        verbose_name = _("Player")
        verbose_name_plural = _("Players")

    def clean(self):
        super().clean()
        # Force role to be PLAYER
        self.role = 'PLAYER'

    def __str__(self):
        return f"{self.get_full_name()} - {self.membership_number or 'No Membership Number'}"

    def save(self, *args, **kwargs):
        # Force role to be PLAYER before saving
        self.role = 'PLAYER'
        super().save(*args, **kwargs)

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
                            choices=STATUS_CHOICES, default='INACTIVE')
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

class Transfer(TimeStampedModel):
    """Represents a player transfer between clubs"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]

    player = models.ForeignKey(Player, on_delete=models.CASCADE, 
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
        current_registration = PlayerClubRegistration.objects.filter(
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
            PlayerClubRegistration.objects.filter(
                player=self.player,
                club=self.from_club,
                status='ACTIVE'
            ).update(status='TRANSFERRED')

            # Create new registration with to_club
            PlayerClubRegistration.objects.create(
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
        app_label = 'membership'
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