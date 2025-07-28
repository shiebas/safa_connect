from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import timezone
from .geography.models import GeographyClub, Province, Region, LocalFootballAssociation, NationalFederation, Association
from .member.models import Member  # Assuming this is a separate model

class MemberRegistration(models.Model):
    """
    Represents a member's registration with a specific club after SAFA approval.
    Combines member data, club info, and registration status.
    """

    # Statuses for the registration process
    REGISTRATION_STATUS = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED',:
            'Suspended'),
        ('TRANSFERRED', 'Transferred'),
    ]

    MEMBER_REGISTRATION_STATUS = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELED', 'Canceled'),
    ]

    # Member reference
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='member_registrations',
        help_text=_("The member being registered")
    )

    # Club reference
    club = models.ForeignKey(
        GeographyClub,
        on_delete=models.CASCADE,
        related_name='member_club_registrations',
        help_text=_("The club this member is registered with")
    )

    # Registration details
    registration_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=20,
        choices=REGISTRATION_STATUS,
        default='PENDING'
    )
    member_status = models.CharField(
        max_length=20,
        choices=MEMBER_REGISTRATION_STATUS,
        default='PENDING'
    )

    # SAFA compliance fields
    season_config = models.ForeignKey(
        'geography.SAFASeasonConfig',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='member_registrations',
        help_text=_("Season this registration belongs to (for SAFA fees)")
    )
    registered_by_admin = models.BooleanField(
        _("Registered by Admin"),
        default=False,
        help_text=_("Whether this member was registered by a club administrator")
    )
    registering_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='registered_members',
        help_text=_("The club administrator who registered this member")
    )

    # Geography fields
    province = models.ForeignKey(
        'geography.Province', 
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )
    region = models.ForeignKey(
        'geography.Region', 
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )
    lfa = models.ForeignKey(
        'geography.LocalFootballAssociation', 
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )
    national_federation = models.ForeignKey(
        'geography.NationalFederation',
        on_delete=models.PROTECT,
        null=False, blank=False,
        default=1,
        help_text=_("The national federation this member belongs to")
    )
    association = models.ForeignKey(
        'geography.Association', 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='associated_members'
    )

    # Emergency contact
    emergency_contact = models.CharField(
        _("Emergency Contact"),
        max_length=100, blank=True
    )
    emergency_phone = models.CharField(
        _("Emergency Contact Phone"),
        max_length=20, blank=True
    )
    medical_notes = models.TextField(_("Medical Notes"), blank=True)

    # Additional fields for club registration
    position = models.CharField(max_length=50, blank=True)
    jersey_number = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Member Registration")
        verbose_name_plural = _("Member Registrations")
        unique_together = ('member', 'club')

    def __str__(self):
        return f"{self.member.get_full_name()} - {self.club.name}"

    def clean(self):
        super().clean()
        # Ensure member is approved before club registration
        if self.member.status != 'ACTIVE':
            raise ValidationError(_("Only approved SAFA members can register with clubs"))
