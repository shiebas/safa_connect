from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from geography.models import LocalFootballAssociation, Region
from accounts.models import CustomUser
import uuid

class Competition(models.Model):
    COMPETITION_TYPES = [
        ('league', 'League'),
        ('cup', 'Cup/Knockout'),
        ('tournament', 'Tournament'),
    ]
    
    COMPETITION_LEVELS = [
        ('regional', 'Regional'),
        ('provincial', 'Provincial'), 
        ('national', 'National'),
        ('local', 'Local LFA'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    safa_id = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=50, blank=True)
    competition_type = models.CharField(max_length=20, choices=COMPETITION_TYPES)
    level = models.CharField(max_length=20, choices=COMPETITION_LEVELS)
    
    # Geography
    region = models.ForeignKey(Region, on_delete=models.CASCADE, null=True, blank=True)
    lfa = models.ForeignKey(LocalFootballAssociation, on_delete=models.CASCADE, null=True, blank=True)
    
    # Season info
    season_year = models.CharField(max_length=9, help_text="e.g., 2025/2026")
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Sponsor
    sponsor_name = models.CharField(max_length=200, blank=True)
    sponsor_logo = models.ImageField(upload_to='competitions/sponsors/', blank=True)
    
    # Competition settings
    max_teams = models.PositiveIntegerField(default=16)
    rounds = models.PositiveIntegerField(default=1, help_text="Number of rounds (1=single, 2=double)")
    points_win = models.PositiveIntegerField(default=3)
    points_draw = models.PositiveIntegerField(default=1) 
    points_loss = models.PositiveIntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    registration_open = models.BooleanField(default=True)
    fixtures_generated = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=timezone.now)  # Fixed this line
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-season_year', 'name']
        
    def __str__(self):
        sponsor = f" ({self.sponsor_name})" if self.sponsor_name else ""
        return f"{self.name}{sponsor} - {self.season_year}"
    
    def save(self, *args, **kwargs):
        if not self.safa_id:
            # Generate SAFA ID: COMP-YYYY-XXX
            year = self.season_year.split('/')[0] if '/' in self.season_year else self.season_year
            count = Competition.objects.filter(season_year__startswith=year).count() + 1
            self.safa_id = f"COMP-{year}-{count:03d}"
        super().save(*args, **kwargs)

class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    safa_id = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=20, blank=True)
    
    # Club details
    lfa = models.ForeignKey(LocalFootballAssociation, on_delete=models.CASCADE)
    home_ground = models.CharField(max_length=200, blank=True)
    team_logo = models.ImageField(upload_to='teams/logos/', blank=True)
    
    # Colors
    home_kit_color = models.CharField(max_length=50, default='White')
    away_kit_color = models.CharField(max_length=50, default='Blue')
    
    # Contact
    manager_name = models.CharField(max_length=200, blank=True)
    contact_person = models.CharField(max_length=200, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({self.lfa.name})"
    
    def save(self, *args, **kwargs):
        if not self.safa_id:
            count = Team.objects.count() + 1
            self.safa_id = f"TEAM-{count:04d}"
        super().save(*args, **kwargs)

class CompetitionTeam(models.Model):
    """Teams registered for a specific competition"""
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='teams')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    
    # Registration
    registration_date = models.DateTimeField(auto_now_add=True)
    registration_fee_paid = models.BooleanField(default=False)
    
    # League stats
    played = models.PositiveIntegerField(default=0)
    won = models.PositiveIntegerField(default=0)
    drawn = models.PositiveIntegerField(default=0)
    lost = models.PositiveIntegerField(default=0)
    goals_for = models.PositiveIntegerField(default=0)
    goals_against = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['competition', 'team']
        ordering = ['-points', '-goals_for', 'goals_against']
        
    def __str__(self):
        return f"{self.team.name} in {self.competition.name}"
    
    @property
    def goal_difference(self):
        return self.goals_for - self.goals_against

class Fixture(models.Model):
    FIXTURE_STATUS = [
        ('scheduled', 'Scheduled'),
        ('live', 'Live'),
        ('completed', 'Completed'),
        ('postponed', 'Postponed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='fixtures')
    
    # Teams
    home_team = models.ForeignKey(CompetitionTeam, on_delete=models.CASCADE, related_name='home_fixtures')
    away_team = models.ForeignKey(CompetitionTeam, on_delete=models.CASCADE, related_name='away_fixtures')
    
    # Fixture details
    round_number = models.PositiveIntegerField(default=1)
    match_day = models.PositiveIntegerField(default=1)
    venue = models.CharField(max_length=200, blank=True)
    
    # Scheduling
    scheduled_date = models.DateTimeField()
    kickoff_time = models.TimeField()
    
    # Results
    status = models.CharField(max_length=20, choices=FIXTURE_STATUS, default='scheduled')
    home_score = models.PositiveIntegerField(null=True, blank=True)
    away_score = models.PositiveIntegerField(null=True, blank=True)
    
    # Officials
    referee = models.CharField(max_length=200, blank=True)
    assistant_ref_1 = models.CharField(max_length=200, blank=True)
    assistant_ref_2 = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_date', 'kickoff_time']
        
    def __str__(self):
        score = ""
        if self.status == 'completed' and self.home_score is not None:
            score = f" {self.home_score}-{self.away_score}"
        return f"{self.home_team.team.short_name or self.home_team.team.name} vs {self.away_team.team.short_name or self.away_team.team.name}{score}"

class MatchEvent(models.Model):
    EVENT_TYPES = [
        ('goal', 'Goal'),
        ('yellow_card', 'Yellow Card'),
        ('red_card', 'Red Card'),
        ('substitution', 'Substitution'),
        ('penalty', 'Penalty'),
        ('own_goal', 'Own Goal'),
    ]
    
    fixture = models.ForeignKey(Fixture, on_delete=models.CASCADE, related_name='events')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    player_name = models.CharField(max_length=200)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    minute = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(120)])
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['minute']
        
    def __str__(self):
        return f"{self.event_type} - {self.player_name} ({self.minute}')"
