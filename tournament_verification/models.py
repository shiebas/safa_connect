from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

User = get_user_model()

class TournamentRegistration(models.Model):
    """Model for tournament registrations with photo verification"""
    VERIFICATION_STATUS_CHOICES = [
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Verified'),
        ('FAILED', 'Verification Failed'),
        ('MANUAL_REVIEW', 'Manual Review Required'),
        ('REJECTED', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey('tournament_verification.TournamentCompetition', on_delete=models.CASCADE, related_name='registrations')
    
    # Team Selection (REQUIRED)
    team = models.ForeignKey('tournament_verification.TournamentTeam', on_delete=models.CASCADE, 
                            related_name='registrations', null=True, blank=True,
                            help_text="Team the player is registering for")
    
    # Player information
    player = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, 
                              help_text="Registered player from system (optional)")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    id_number = models.CharField(max_length=20, help_text="ID Number or Passport")
    
    # Photo verification
    live_photo = models.ImageField(upload_to='tournament_live_photos/', 
                                  help_text="Photo taken during registration")
    stored_photo = models.ImageField(upload_to='tournament_stored_photos/', null=True, blank=True,
                                   help_text="Photo from player's profile (if registered)")
    
    # Verification results
    verification_score = models.FloatField(null=True, blank=True, 
                                         validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
                                         help_text="Confidence score from facial recognition (0-1)")
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, 
                                         default='PENDING')
    verification_notes = models.TextField(blank=True, help_text="Notes from verification process")
    
    # Registration details
    registration_type = models.CharField(max_length=20, choices=[
        ('SYSTEM_PLAYER', 'Registered System Player'),
        ('WALK_IN', 'Walk-in Registration'),
    ], default='WALK_IN')
    
    # Timestamps
    registered_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='verified_registrations')
    
    class Meta:
        ordering = ['-registered_at']
        verbose_name = "Tournament Registration"
        verbose_name_plural = "Tournament Registrations"
        unique_together = ['tournament', 'id_number']  # Prevent duplicate registrations
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.tournament.name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_verified(self):
        return self.verification_status == 'VERIFIED'
    
    @property
    def verification_confidence_percentage(self):
        if self.verification_score is not None:
            return round(self.verification_score * 100, 1)
        return None

class VerificationLog(models.Model):
    """Log for tracking verification attempts and results"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration = models.ForeignKey(TournamentRegistration, on_delete=models.CASCADE, 
                                   related_name='verification_logs')
    attempt_number = models.PositiveIntegerField(default=1)
    verification_score = models.FloatField(null=True, blank=True)
    verification_status = models.CharField(max_length=20, choices=TournamentRegistration.VERIFICATION_STATUS_CHOICES)
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Verification Log"
        verbose_name_plural = "Verification Logs"
    
    def __str__(self):
        return f"Verification {self.attempt_number} for {self.registration.full_name}"
