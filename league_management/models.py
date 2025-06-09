from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from geography.models import LocalFootballAssociation, Region
from accounts.models import CustomUser
import uuid

class CompetitionCategory(models.Model):
    """Competition categories like ABC Motsepe League, SAFA Hollywood Bets Regional, Women's League"""
    name = models.CharField(max_length=200)  # e.g., "ABC Motsepe League", "SAFA Hollywood Bets Regional"
    short_name = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    
    # Gender and age categories
    GENDER_CHOICES = [
        ('men', 'Men'),
        ('women', 'Women'),
        ('mixed', 'Mixed'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='men')
    
    AGE_CATEGORIES = [
        ('senior', 'Senior'),
        ('u21', 'Under 21'),
        ('u19', 'Under 19'),
        ('u17', 'Under 17'),
    ]
    age_category = models.CharField(max_length=10, choices=AGE_CATEGORIES, default='senior')
    
    # Hierarchy level
    LEVELS = [
        ('national', 'National'),
        ('regional', 'Regional'),
        ('provincial', 'Provincial'),
        ('local', 'Local'),
    ]
    level = models.CharField(max_length=20, choices=LEVELS)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['level', 'gender', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.get_gender_display()} {self.get_age_category_display()})"

class Competition(models.Model):
    """Specific competition instance for a region/season"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    safa_id = models.CharField(max_length=20, unique=True, blank=True)
    
    # Competition details
    category = models.ForeignKey(CompetitionCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)  # e.g., "ABC Motsepe League - Eastern Cape 2024/25"
    season_year = models.CharField(max_length=9, help_text="e.g., 2024/2025")
    
    # Geography - add related_name to avoid clash
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='league_competitions')
    
    # Season dates
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Sponsor
    main_sponsor = models.CharField(max_length=200, blank=True)  # e.g., "Hollywood Bets"
    sponsor_logo = models.ImageField(upload_to='competitions/sponsors/', blank=True)
    
    # Competition structure
    has_groups = models.BooleanField(default=False, help_text="Does this competition have groups/streams?")
    teams_per_group = models.PositiveIntegerField(default=18, help_text="Teams per group/stream")
    
    # Points system
    points_win = models.PositiveIntegerField(default=3)
    points_draw = models.PositiveIntegerField(default=1)
    points_loss = models.PositiveIntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    registration_open = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-season_year', 'region', 'category']
        
    def __str__(self):
        return f"{self.category.name} - {self.region.name} {self.season_year}"
    
    def save(self, *args, **kwargs):
        if not self.safa_id:
            year = self.season_year.split('/')[0] if '/' in self.season_year else self.season_year
            region_code = self.region.name[:3].upper()
            category_code = self.category.short_name or self.category.name[:3].upper()
            count = Competition.objects.filter(
                season_year__startswith=year,
                region=self.region,
                category=self.category
            ).count() + 1
            self.safa_id = f"{category_code}-{region_code}-{year}-{count:02d}"
        super().save(*args, **kwargs)

class CompetitionGroup(models.Model):
    """Groups/Streams within a competition (e.g., Group A, Stream 1)"""
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='groups')
    
    name = models.CharField(max_length=50)  # e.g., "Group A", "Stream 1", "Pool North"
    description = models.TextField(blank=True)
    
    # Group can be geographical or random
    GROUP_TYPES = [
        ('geographical', 'Geographical'),
        ('random', 'Random Draw'),
        ('seeded', 'Seeded'),
    ]
    group_type = models.CharField(max_length=20, choices=GROUP_TYPES, default='geographical')
    
    max_teams = models.PositiveIntegerField(default=18)
    
    class Meta:
        unique_together = ['competition', 'name']
        ordering = ['competition', 'name']
        
    def __str__(self):
        return f"{self.competition.category.short_name or self.competition.category.name} {self.name} - {self.competition.region.name}"

class Team(models.Model):
    """Teams in the SAFA system"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    safa_id = models.CharField(max_length=20, unique=True, blank=True)
    
    # Team details
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=20, blank=True)
    nickname = models.CharField(max_length=100, blank=True)
    
    # Geography - add related_name to avoid clash
    lfa = models.ForeignKey(LocalFootballAssociation, on_delete=models.CASCADE, related_name='league_teams')
    home_ground = models.CharField(max_length=200, blank=True)
    
    # Team management
    manager_name = models.CharField(max_length=200, blank=True)
    coach_name = models.CharField(max_length=200, blank=True)
    contact_person = models.CharField(max_length=200, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    
    # Club colors and logo
    primary_color = models.CharField(max_length=50, default='Blue')
    secondary_color = models.CharField(max_length=50, default='White')
    team_logo = models.ImageField(upload_to='teams/logos/', blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({self.lfa.name})"
    
    def save(self, *args, **kwargs):
        if not self.safa_id:
            region_code = self.lfa.region.name[:3].upper()
            count = Team.objects.filter(lfa__region=self.lfa.region).count() + 1
            self.safa_id = f"TEAM-{region_code}-{count:04d}"
        super().save(*args, **kwargs)

class CompetitionTeam(models.Model):
    """Teams registered for a specific competition/group"""
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='teams')
    group = models.ForeignKey(CompetitionGroup, on_delete=models.CASCADE, null=True, blank=True, related_name='teams')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    
    # Registration
    registration_date = models.DateTimeField(auto_now_add=True)
    registration_fee_paid = models.BooleanField(default=False)
    
    # League statistics
    played = models.PositiveIntegerField(default=0)
    won = models.PositiveIntegerField(default=0)
    drawn = models.PositiveIntegerField(default=0)
    lost = models.PositiveIntegerField(default=0)
    goals_for = models.PositiveIntegerField(default=0)
    goals_against = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=0)
    
    # Additional stats
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['competition', 'team']
        ordering = ['-points', '-goals_for', 'goals_against', 'team__name']
        
    def __str__(self):
        group_info = f" ({self.group.name})" if self.group else ""
        return f"{self.team.name} in {self.competition.category.short_name or self.competition.category.name}{group_info}"
    
    @property
    def goal_difference(self):
        return self.goals_for - self.goals_against
    
    @property
    def league_position(self):
        """Calculate current league position"""
        if self.group:
            teams = self.group.teams.all().order_by('-points', '-goals_for', 'goals_against')
        else:
            teams = self.competition.teams.all().order_by('-points', '-goals_for', 'goals_against')
        
        for i, team in enumerate(teams, 1):
            if team.id == self.id:
                return i
        return None

class Match(models.Model):
    """Individual matches in competitions"""
    MATCH_STATUS = [
        ('scheduled', 'Scheduled'),
        ('live', 'Live'),
        ('completed', 'Completed'),
        ('postponed', 'Postponed'),
        ('cancelled', 'Cancelled'),
        ('abandoned', 'Abandoned'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='matches')
    group = models.ForeignKey(CompetitionGroup, on_delete=models.CASCADE, null=True, blank=True, related_name='matches')
    
    # Teams
    home_team = models.ForeignKey(CompetitionTeam, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(CompetitionTeam, on_delete=models.CASCADE, related_name='away_matches')
    
    # Match details
    round_number = models.PositiveIntegerField(default=1)
    match_day = models.PositiveIntegerField(default=1)
    
    # Scheduling
    match_date = models.DateField()
    kickoff_time = models.TimeField()
    venue = models.CharField(max_length=200, blank=True)
    
    # Results
    status = models.CharField(max_length=20, choices=MATCH_STATUS, default='scheduled')
    home_score = models.PositiveIntegerField(null=True, blank=True)
    away_score = models.PositiveIntegerField(null=True, blank=True)
    
    # Officials
    referee = models.CharField(max_length=200, blank=True)
    assistant_ref_1 = models.CharField(max_length=200, blank=True)
    assistant_ref_2 = models.CharField(max_length=200, blank=True)
    fourth_official = models.CharField(max_length=200, blank=True)
    
    # Match info
    attendance = models.PositiveIntegerField(null=True, blank=True)
    weather_conditions = models.CharField(max_length=100, blank=True)
    pitch_conditions = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['match_date', 'kickoff_time']
        
    def __str__(self):
        if self.status == 'completed' and self.home_score is not None:
            return f"{self.home_team.team.short_name or self.home_team.team.name} {self.home_score}-{self.away_score} {self.away_team.team.short_name or self.away_team.team.name}"
        return f"{self.home_team.team.short_name or self.home_team.team.name} vs {self.away_team.team.short_name or self.away_team.team.name}"

class MatchEvent(models.Model):
    """Events that occur during matches (goals, cards, substitutions)"""
    EVENT_TYPES = [
        ('goal', 'Goal'),
        ('own_goal', 'Own Goal'),
        ('penalty_goal', 'Penalty Goal'),
        ('yellow_card', 'Yellow Card'),
        ('red_card', 'Red Card'),
        ('substitution', 'Substitution'),
        ('penalty_miss', 'Penalty Miss'),
    ]
    
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='events')
    team = models.ForeignKey(CompetitionTeam, on_delete=models.CASCADE)
    
    # Event details
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    minute = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(120)])
    player_name = models.CharField(max_length=200)
    
    # Additional details for substitutions
    substitute_in = models.CharField(max_length=200, blank=True, help_text="Player coming on")
    substitute_out = models.CharField(max_length=200, blank=True, help_text="Player going off")
    
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['minute', 'created_at']
        
    def __str__(self):
        if self.event_type == 'substitution':
            return f"{self.minute}' - SUB: {self.substitute_in} for {self.substitute_out} ({self.team.team.short_name})"
        return f"{self.minute}' - {self.get_event_type_display()}: {self.player_name} ({self.team.team.short_name})"
