from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.conf import settings  # Add this import
from django.utils import timezone
from django_extensions.db.models import TimeStampedModel
from utils.models import ModelWithLogo
from geography.models import (
    NationalFederation, Association, LocalFootballAssociation, Club
)

# Create your models here.

class CompetitionType(TimeStampedModel):
    """Defines different types of competitions (League, Cup, Tournament, etc.)"""
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    format = models.CharField(_('Format'), max_length=20, choices=[
        ('LEAGUE', _('League')),
        ('KNOCKOUT', _('Knockout')),
        ('GROUP', _('Group Stage')),
        ('HYBRID', _('Hybrid')),
    ])
    
    class Meta:
        verbose_name = _('Competition Type')
        verbose_name_plural = _('Competition Types')
        
    def __str__(self):
        return self.name

class CompetitionLevel(TimeStampedModel):
    """Defines the level at which a competition operates (National, Provincial, etc.)"""
    name = models.CharField(_('Name'), max_length=100)
    level_order = models.PositiveIntegerField(_('Level Order'), help_text=_('Lower numbers represent higher levels'))
    description = models.TextField(_('Description'), blank=True)
    
    class Meta:
        verbose_name = _('Competition Level')
        verbose_name_plural = _('Competition Levels')
        ordering = ['level_order']
        
    def __str__(self):
        return self.name

class CompetitionCategory(TimeStampedModel):
    """Categorizes competitions by gender, age group, etc."""
    name = models.CharField(_('Name'), max_length=100)
    gender = models.CharField(_('Gender'), max_length=1, choices=[
        ('M', _('Male')),
        ('F', _('Female')),
        ('X', _('Mixed')),
    ])
    min_age = models.PositiveIntegerField(_('Minimum Age'), null=True, blank=True)
    max_age = models.PositiveIntegerField(_('Maximum Age'), null=True, blank=True)
    description = models.TextField(_('Description'), blank=True)
    
    class Meta:
        verbose_name = _('Competition Category')
        verbose_name_plural = _('Competition Categories')
        
    def __str__(self):
        return self.name

class Competition(TimeStampedModel):
    """Core competition model representing a specific league/cup/tournament"""
    name = models.CharField(_('Name'), max_length=100)
    short_name = models.CharField(_('Short Name'), max_length=50, blank=True)
    competition_type = models.ForeignKey(CompetitionType, on_delete=models.PROTECT, null=True, blank=True)  # Optional for now
    competition_level = models.ForeignKey(CompetitionLevel, on_delete=models.PROTECT, null=True, blank=True)  # Optional for now
    category = models.ForeignKey(CompetitionCategory, on_delete=models.PROTECT, null=True, blank=True)  # Optional for now
    
    # Geographic scope - all optional during development
    managed_by = models.CharField(_('Managed By'), max_length=20, choices=[
        ('NF', _('National Federation')),
        ('ASSOC', _('Association')),
        ('LFA', _('Local Football Association')),
        ('OTHER', _('Other Organization')),
    ], default='OTHER')
    national_federation = models.ForeignKey('geography.NationalFederation', on_delete=models.SET_NULL, null=True, blank=True)
    association = models.ForeignKey('geography.Association', on_delete=models.SET_NULL, null=True, blank=True)
    local_football_association = models.ForeignKey('geography.LocalFootballAssociation', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Competition rules
    points_win = models.PositiveIntegerField(_('Points for Win'), default=3)
    points_draw = models.PositiveIntegerField(_('Points for Draw'), default=1)
    points_loss = models.PositiveIntegerField(_('Points for Loss'), default=0)
    
    description = models.TextField(_('Description'), blank=True)
    website = models.URLField(_('Website'), blank=True)
    
    class Meta:
        verbose_name = _('Competition')
        verbose_name_plural = _('Competitions')
        
    def __str__(self):
        return self.name
    
    # Comment out validation during development
    # def clean(self):
    #     """Ensure proper organization is selected based on managed_by"""
    #     errors = {}
    #     
    #     if self.managed_by == 'NF' and not self.national_federation:
    #         errors['national_federation'] = _('National Federation must be specified')
    #     
    #     if self.managed_by == 'ASSOC' and not self.association:
    #         errors['association'] = _('Association must be specified')
    #     
    #     if self.managed_by == 'LFA' and not self.local_football_association:
    #         errors['local_football_association'] = _('Local Football Association must be specified')
    #     
    #     if errors:
    #         raise ValidationError(errors)

class Season(TimeStampedModel):
    """Represents a specific season of a competition"""
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='seasons')
    name = models.CharField(_('Name'), max_length=100)  # e.g., "2024/25 Season"
    start_date = models.DateField(_('Start Date'), null=True, blank=True)  # Optional during development
    end_date = models.DateField(_('End Date'), null=True, blank=True)  # Optional during development
    registration_open = models.DateField(_('Registration Opens'), null=True, blank=True)  # Optional
    registration_close = models.DateField(_('Registration Closes'), null=True, blank=True)  # Optional
    is_active = models.BooleanField(_('Active Season'), default=True)  # Default to active
    
    class Meta:
        verbose_name = _('Season')
        verbose_name_plural = _('Seasons')
        ordering = ['-start_date']
        
    def __str__(self):
        return f"{self.competition.name} - {self.name}"
    
    def clean(self):
        # Only validate if both dates are provided
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': _('End date must be after start date')})
        
        if self.registration_close and self.start_date and self.registration_close > self.start_date:
            raise ValidationError({'registration_close': _('Registration must close before season starts')})

class TeamRegistration(TimeStampedModel):
    """Represents a team registered for a specific season of a competition"""
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='team_registrations')
    club = models.ForeignKey('geography.Club', on_delete=models.CASCADE)
    team_name = models.CharField(_('Team Name'), max_length=100, help_text=_('Can differ from club name for multiple teams'))
    registration_date = models.DateField(_('Registration Date'), null=True, blank=True)  # Make this optional
    status = models.CharField(_('Status'), max_length=20, choices=[
        ('PENDING', _('Pending Approval')),
        ('APPROVED', _('Approved')),
        ('REJECTED', _('Rejected')),
        ('WITHDRAWN', _('Withdrawn')),
    ], default='APPROVED')  # Default to approved during development
    notes = models.TextField(_('Notes'), blank=True)
    
    class Meta:
        verbose_name = _('Team Registration')
        verbose_name_plural = _('Team Registrations')
        unique_together = ['season', 'club', 'team_name']
        
    def __str__(self):
        return f"{self.team_name} - {self.season}"

class Venue(TimeStampedModel):
    """Represents a venue where matches are played"""
    name = models.CharField(_('Name'), max_length=100)
    address = models.TextField(_('Address'), blank=True)
    capacity = models.PositiveIntegerField(_('Capacity'), null=True, blank=True)
    surface_type = models.CharField(_('Surface Type'), max_length=50, blank=True)
    local_football_association = models.ForeignKey('geography.LocalFootballAssociation', on_delete=models.SET_NULL, null=True, blank=True)
    location_coordinates = models.CharField(_('GPS Coordinates'), max_length=50, blank=True)
    
    class Meta:
        verbose_name = _('Venue')
        verbose_name_plural = _('Venues')
        
    def __str__(self):
        return self.name

class MatchOfficial(TimeStampedModel):
    """Represents referees and other match officials"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # Changed from 'auth.User' to settings.AUTH_USER_MODEL
        on_delete=models.CASCADE
    )
    qualification_level = models.CharField(_('Qualification'), max_length=50, blank=True)
    official_number = models.CharField(_('Official Number'), max_length=20, blank=True)
    local_football_association = models.ForeignKey('geography.LocalFootballAssociation', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(_('Active'), default=True)
    notes = models.TextField(_('Notes'), blank=True)
    
    class Meta:
        verbose_name = _('Match Official')
        verbose_name_plural = _('Match Officials')
        
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.qualification_level})"

class Fixture(TimeStampedModel):
    """Represents a scheduled match between two teams"""
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='fixtures')
    home_team = models.ForeignKey(TeamRegistration, on_delete=models.CASCADE, related_name='home_fixtures')
    away_team = models.ForeignKey(TeamRegistration, on_delete=models.CASCADE, related_name='away_fixtures')
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, blank=True)
    
    scheduled_date = models.DateField(_('Scheduled Date'), null=True, blank=True)  # Optional during development
    scheduled_time = models.TimeField(_('Scheduled Time'), null=True, blank=True)  # Optional during development
    
    # Make all official fields optional
    referee = models.ForeignKey(MatchOfficial, on_delete=models.SET_NULL, null=True, blank=True, related_name='fixtures_as_referee')
    assistant_referee1 = models.ForeignKey(MatchOfficial, on_delete=models.SET_NULL, null=True, blank=True, related_name='fixtures_as_ar1')
    assistant_referee2 = models.ForeignKey(MatchOfficial, on_delete=models.SET_NULL, null=True, blank=True, related_name='fixtures_as_ar2')
    fourth_official = models.ForeignKey(MatchOfficial, on_delete=models.SET_NULL, null=True, blank=True, related_name='fixtures_as_fourth')
    
    status = models.CharField(_('Status'), max_length=20, choices=[
        ('SCHEDULED', _('Scheduled')),
        ('POSTPONED', _('Postponed')),
        ('COMPLETED', _('Completed')),
        ('CANCELLED', _('Cancelled')),
    ], default='SCHEDULED')
    
    round_name = models.CharField(_('Round'), max_length=50, blank=True, help_text=_('e.g., "Round 1", "Quarter Final"'))
    leg = models.PositiveIntegerField(_('Leg'), default=1, help_text=_('For two-legged ties'))
    
    class Meta:
        verbose_name = _('Fixture')
        verbose_name_plural = _('Fixtures')
        ordering = ['scheduled_date', 'scheduled_time']
        
    def __str__(self):
        return f"{self.home_team.team_name} vs {self.away_team.team_name} - {self.scheduled_date or 'TBD'}"

class MatchResult(TimeStampedModel):
    """Stores the result of a completed match"""
    fixture = models.OneToOneField(Fixture, on_delete=models.CASCADE, related_name='result')
    
    home_score = models.PositiveIntegerField(_('Home Score'), null=True, blank=True)
    away_score = models.PositiveIntegerField(_('Away Score'), null=True, blank=True)
    home_score_ht = models.PositiveIntegerField(_('Home Score HT'), null=True, blank=True)
    away_score_ht = models.PositiveIntegerField(_('Away Score HT'), null=True, blank=True)
    
    home_penalties = models.PositiveIntegerField(_('Home Penalties'), null=True, blank=True)
    away_penalties = models.PositiveIntegerField(_('Away Penalties'), null=True, blank=True)
    
    outcome = models.CharField(_('Outcome'), max_length=20, choices=[
        ('HOME_WIN', _('Home Win')),
        ('AWAY_WIN', _('Away Win')),
        ('DRAW', _('Draw')),
        ('HOME_FORFEIT', _('Home Team Forfeit')),
        ('AWAY_FORFEIT', _('Away Team Forfeit')),
        ('ABANDONED', _('Match Abandoned')),
    ], null=True, blank=True)
    
    verified = models.BooleanField(_('Verified'), default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Changed from 'auth.User' to settings.AUTH_USER_MODEL
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='verified_results'
    )
    verified_date = models.DateTimeField(_('Verification Date'), null=True, blank=True)
    
    notes = models.TextField(_('Match Notes'), blank=True)
    
    class Meta:
        verbose_name = _('Match Result')
        verbose_name_plural = _('Match Results')
        
    def __str__(self):
        return f"{self.fixture.home_team.team_name} {self.home_score}-{self.away_score} {self.fixture.away_team.team_name}"
    
    def save(self, *args, **kwargs):
        # Determine outcome based on scores
        if self.home_score is not None and self.away_score is not None:
            if self.home_score > self.away_score:
                self.outcome = 'HOME_WIN'
            elif self.away_score > self.home_score:
                self.outcome = 'AWAY_WIN'
            else:
                self.outcome = 'DRAW'
                
        super().save(*args, **kwargs)

class Standing(TimeStampedModel):
    """Represents a team's standing in a league competition"""
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='standings')
    team = models.ForeignKey(TeamRegistration, on_delete=models.CASCADE)
    
    # Basic standings
    played = models.PositiveIntegerField(_('Played'), default=0)
    won = models.PositiveIntegerField(_('Won'), default=0)
    drawn = models.PositiveIntegerField(_('Drawn'), default=0)
    lost = models.PositiveIntegerField(_('Lost'), default=0)
    
    goals_for = models.PositiveIntegerField(_('Goals For'), default=0)
    goals_against = models.PositiveIntegerField(_('Goals Against'), default=0)
    
    points = models.PositiveIntegerField(_('Points'), default=0)
    
    # Additional fields for tiebreakers
    goal_difference = models.IntegerField(_('Goal Difference'), default=0)
    fair_play_points = models.IntegerField(_('Fair Play Points'), default=0)
    
    # For manual adjustments
    points_deducted = models.PositiveIntegerField(_('Points Deducted'), default=0)
    deduction_reason = models.TextField(_('Deduction Reason'), blank=True)
    
    position = models.PositiveIntegerField(_('Position'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Standing')
        verbose_name_plural = _('Standings')
        unique_together = ['season', 'team']
        ordering = ['-points', '-goal_difference', '-goals_for', 'team__team_name']
        
    def __str__(self):
        return f"{self.team.team_name} - {self.season.competition.name}"
    
    def update_stats(self):
        """Updates team statistics based on match results"""
        self.played = self.team.home_fixtures.filter(status='COMPLETED').count() + self.team.away_fixtures.filter(status='COMPLETED').count()
        
        # Calculate wins, draws, losses
        home_results = MatchResult.objects.filter(fixture__home_team=self.team, fixture__status='COMPLETED')
        away_results = MatchResult.objects.filter(fixture__away_team=self.team, fixture__status='COMPLETED')
        
        self.won = home_results.filter(outcome='HOME_WIN').count() + away_results.filter(outcome='AWAY_WIN').count()
        self.drawn = home_results.filter(outcome='DRAW').count() + away_results.filter(outcome='DRAW').count()
        self.lost = home_results.filter(outcome='AWAY_WIN').count() + away_results.filter(outcome='HOME_WIN').count()
        
        # Calculate goals
        self.goals_for = sum([r.home_score or 0 for r in home_results]) + sum([r.away_score or 0 for r in away_results])
        self.goals_against = sum([r.away_score or 0 for r in home_results]) + sum([r.home_score or 0 for r in away_results])
        
        # Calculate points and goal difference
        self.goal_difference = self.goals_for - self.goals_against
        self.points = (self.won * self.season.competition.points_win) + (self.drawn * self.season.competition.points_draw) - self.points_deducted
        
        self.save()
