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
    safa_id = models.CharField(max_length=5, unique=True, blank=True)  # Changed from 20 to 5
    
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
            # Generate 5-digit random alphanumeric SAFA ID (A-Z, 0-9)
            import string
            import random
            
            while True:
                chars = string.ascii_uppercase + string.digits
                safa_id = ''.join(random.choices(chars, k=5))
                
                if not Competition.objects.filter(safa_id=safa_id).exists():
                    self.safa_id = safa_id
                    break
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
    safa_id = models.CharField(max_length=5, unique=True, blank=True)  # Changed from 20 to 5
    
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
            # Generate 5-digit random alphanumeric SAFA ID (A-Z, 0-9)
            import string
            import random
            
            while True:
                # Generate 5-character random string with capitals and numbers
                chars = string.ascii_uppercase + string.digits
                safa_id = ''.join(random.choices(chars, k=5))
                
                # Check if this ID already exists
                if not Team.objects.filter(safa_id=safa_id).exists():
                    self.safa_id = safa_id
                    break
        
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
    match_number = models.CharField(max_length=10, unique=True, blank=True)  # Sequential match numbers
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
    
    def save(self, *args, **kwargs):
        if not self.match_number:
            # Generate sequential match number for the competition
            year = self.competition.season_year.split('/')[0] if '/' in self.competition.season_year else self.competition.season_year
            count = Match.objects.filter(competition=self.competition).count() + 1
            self.match_number = f"M{year}-{count:04d}"  # e.g., M2024-0001
        super().save(*args, **kwargs)

class MatchEvent(models.Model):
    """Events that occur during matches (goals, cards, substitutions)"""
    EVENT_TYPES = [
        ('goal', 'Goal'),
        ('own_goal', 'Own Goal'),
        ('penalty_goal', 'Penalty Goal'),
        ('yellow_card', 'Yellow Card'),
        ('red_card', 'Red Card'),
        ('second_yellow', 'Second Yellow Card'),
        ('substitution', 'Substitution'),
        ('penalty_miss', 'Penalty Miss'),
        ('injury', 'Injury'),
        ('offside', 'Offside'),
        ('foul', 'Foul'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='events')
    team = models.ForeignKey(CompetitionTeam, on_delete=models.CASCADE)
    
    # Event details
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    minute = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(120)])
    player_name = models.CharField(max_length=200)
    
    # Additional details for substitutions
    substitute_in = models.CharField(max_length=200, blank=True, help_text="Player coming on")
    substitute_out = models.CharField(max_length=200, blank=True, help_text="Player going off")
    
    # Event details
    description = models.TextField(blank=True)
    is_penalty = models.BooleanField(default=False)
    is_own_goal = models.BooleanField(default=False)
    
    # Recording details
    recorded_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['minute', 'recorded_at']
        
    def __str__(self):
        if self.event_type == 'substitution':
            return f"{self.minute}' - Substitution: {self.substitute_out} → {self.substitute_in}"
        return f"{self.minute}' - {self.get_event_type_display()}: {self.player_name}"

class PlayerStatistics(models.Model):
    """Individual player statistics for a competition"""
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='player_stats')
    team = models.ForeignKey(CompetitionTeam, on_delete=models.CASCADE, related_name='player_stats')
    
    # Player details
    player_name = models.CharField(max_length=200)
    jersey_number = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(99)])
    position = models.CharField(max_length=20, blank=True)  # GK, DEF, MID, FWD
    
    # Statistics
    appearances = models.PositiveIntegerField(default=0)
    goals = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    minutes_played = models.PositiveIntegerField(default=0)
    
    # Goalkeeper specific
    clean_sheets = models.PositiveIntegerField(default=0)
    saves = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['competition', 'team', 'player_name']
        ordering = ['-goals', '-assists', 'player_name']
    
    def __str__(self):
        return f"{self.player_name} ({self.team.team.name})"

class LeagueTable(models.Model):
    """Calculated league table for a competition/group"""
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='league_tables')
    group = models.ForeignKey(CompetitionGroup, on_delete=models.CASCADE, null=True, blank=True, related_name='league_tables')
    team = models.ForeignKey(CompetitionTeam, on_delete=models.CASCADE)
    
    # Table position and stats
    position = models.PositiveIntegerField()
    played = models.PositiveIntegerField(default=0)
    won = models.PositiveIntegerField(default=0)
    drawn = models.PositiveIntegerField(default=0)
    lost = models.PositiveIntegerField(default=0)
    goals_for = models.PositiveIntegerField(default=0)
    goals_against = models.PositiveIntegerField(default=0)
    goal_difference = models.IntegerField(default=0)
    points = models.PositiveIntegerField(default=0)
    
    # Form (last 5 matches)
    form = models.CharField(max_length=5, blank=True)  # e.g., "WWDLW"
    
    # Additional stats
    home_wins = models.PositiveIntegerField(default=0)
    away_wins = models.PositiveIntegerField(default=0)
    clean_sheets = models.PositiveIntegerField(default=0)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['competition', 'group', 'team']
        ordering = ['position']
    
    def __str__(self):
        group_info = f" ({self.group.name})" if self.group else ""
        return f"{self.position}. {self.team.team.name}{group_info}"

class TeamSheet(models.Model):
    """Team sheet for a specific match"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('confirmed', 'Confirmed'),
        ('amended', 'Amended'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='team_sheets')
    team = models.ForeignKey(CompetitionTeam, on_delete=models.CASCADE, related_name='team_sheets')
    
    # Team sheet details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Formation and tactics
    formation = models.CharField(max_length=10, default='4-4-2', help_text="e.g., 4-4-2, 3-5-2")
    captain = models.CharField(max_length=200, blank=True)
    vice_captain = models.CharField(max_length=200, blank=True)
    
    # Notes
    notes = models.TextField(blank=True, help_text="Team notes, tactics, etc.")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['match', 'team']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.team.team.name} - {self.match} ({self.get_status_display()})"
    
    @property
    def is_submitted(self):
        return self.status in ['submitted', 'confirmed', 'amended']
    
    @property
    def can_be_edited(self):
        return self.status in ['draft', 'amended'] and self.match.status == 'scheduled'

class TeamSheetPlayer(models.Model):
    """Individual player in a team sheet"""
    POSITION_CHOICES = [
        ('GK', 'Goalkeeper'),
        ('LB', 'Left Back'),
        ('CB', 'Center Back'),
        ('RB', 'Right Back'),
        ('LWB', 'Left Wing Back'),
        ('RWB', 'Right Wing Back'),
        ('CDM', 'Defensive Midfielder'),
        ('CM', 'Central Midfielder'),
        ('CAM', 'Attacking Midfielder'),
        ('LM', 'Left Midfielder'),
        ('RM', 'Right Midfielder'),
        ('LW', 'Left Winger'),
        ('RW', 'Right Winger'),
        ('ST', 'Striker'),
        ('CF', 'Center Forward'),
        ('SUB', 'Substitute'),
    ]
    
    team_sheet = models.ForeignKey(TeamSheet, on_delete=models.CASCADE, related_name='players')
    player_name = models.CharField(max_length=200)
    jersey_number = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(99)])
    position = models.CharField(max_length=10, choices=POSITION_CHOICES)
    
    # Player status
    is_starting = models.BooleanField(default=True)
    is_captain = models.BooleanField(default=False)
    is_vice_captain = models.BooleanField(default=False)
    
    # Eligibility checks
    is_eligible = models.BooleanField(default=True)
    suspension_reason = models.TextField(blank=True, help_text="Reason if not eligible")
    
    # Match performance (filled during/after match)
    minutes_played = models.PositiveIntegerField(default=0)
    goals_scored = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['team_sheet', 'jersey_number']
        ordering = ['jersey_number']
    
    def __str__(self):
        return f"{self.player_name} (#{self.jersey_number}) - {self.get_position_display()}"

class PlayerDiscipline(models.Model):
    """Track player discipline across competitions"""
    CARD_TYPES = [
        ('yellow', 'Yellow Card'),
        ('red', 'Red Card'),
        ('second_yellow', 'Second Yellow Card'),
    ]
    
    SUSPENSION_TYPES = [
        ('automatic', 'Automatic Suspension'),
        ('manual', 'Manual Suspension'),
        ('appeal', 'Appeal Suspension'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='player_discipline')
    team = models.ForeignKey(CompetitionTeam, on_delete=models.CASCADE, related_name='player_discipline')
    player_name = models.CharField(max_length=200)
    
    # Card tracking
    total_yellow_cards = models.PositiveIntegerField(default=0)
    total_red_cards = models.PositiveIntegerField(default=0)
    total_second_yellows = models.PositiveIntegerField(default=0)
    
    # Suspension tracking
    is_suspended = models.BooleanField(default=False)
    suspension_matches = models.PositiveIntegerField(default=0)
    suspension_until = models.DateField(null=True, blank=True)
    suspension_reason = models.TextField(blank=True)
    suspension_type = models.CharField(max_length=20, choices=SUSPENSION_TYPES, blank=True)
    
    # Reset tracking (for new seasons)
    last_reset_date = models.DateTimeField(auto_now_add=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['competition', 'team', 'player_name']
        ordering = ['-total_red_cards', '-total_yellow_cards', 'player_name']
    
    def __str__(self):
        return f"{self.player_name} ({self.team.team.name}) - {self.total_yellow_cards}Y {self.total_red_cards}R"
    
    @property
    def is_eligible_for_selection(self):
        """Check if player is eligible for selection"""
        from django.utils import timezone
        if self.is_suspended:
            if self.suspension_until and timezone.now().date() <= self.suspension_until:
                return False
            elif self.suspension_matches > 0:
                return False
        return True
    
    def add_card(self, card_type, match=None):
        """Add a card and update suspension status"""
        if card_type == 'yellow':
            self.total_yellow_cards += 1
            # Check for automatic suspension (2 yellow cards)
            if self.total_yellow_cards >= 2:
                self.is_suspended = True
                self.suspension_matches = 1
                self.suspension_type = 'automatic'
                self.suspension_reason = f"Automatic suspension for {self.total_yellow_cards} yellow cards"
        elif card_type == 'red':
            self.total_red_cards += 1
            self.is_suspended = True
            self.suspension_matches = 1
            self.suspension_type = 'automatic'
            self.suspension_reason = "Automatic suspension for red card"
        elif card_type == 'second_yellow':
            self.total_second_yellows += 1
            self.total_red_cards += 1  # Second yellow = red card
            self.is_suspended = True
            self.suspension_matches = 1
            self.suspension_type = 'automatic'
            self.suspension_reason = "Automatic suspension for second yellow card"
        
        self.save()
    
    def serve_suspension(self):
        """Mark one match suspension as served"""
        if self.suspension_matches > 0:
            self.suspension_matches -= 1
            if self.suspension_matches == 0:
                self.is_suspended = False
                self.suspension_reason = ""
            self.save()

class ActivityLog(models.Model):
    """Comprehensive activity logging for the league management system"""
    ACTION_TYPES = [
        ('team_sheet_created', 'Team Sheet Created'),
        ('team_sheet_submitted', 'Team Sheet Submitted'),
        ('team_sheet_amended', 'Team Sheet Amended'),
        ('player_selected', 'Player Selected'),
        ('player_deselected', 'Player Deselected'),
        ('card_issued', 'Card Issued'),
        ('suspension_applied', 'Suspension Applied'),
        ('suspension_served', 'Suspension Served'),
        ('match_event_added', 'Match Event Added'),
        ('match_result_updated', 'Match Result Updated'),
        ('fixture_generated', 'Fixture Generated'),
        ('competition_created', 'Competition Created'),
        ('team_registered', 'Team Registered'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    
    # Related objects
    competition = models.ForeignKey(Competition, on_delete=models.SET_NULL, null=True, blank=True)
    match = models.ForeignKey(Match, on_delete=models.SET_NULL, null=True, blank=True)
    team = models.ForeignKey(CompetitionTeam, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Action details
    description = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['competition', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_action_type_display()} - {self.user} at {self.timestamp}"

class TeamSheetTemplate(models.Model):
    """Templates for quick team sheet creation"""
    name = models.CharField(max_length=200)
    team = models.ForeignKey(CompetitionTeam, on_delete=models.CASCADE, related_name='sheet_templates')
    formation = models.CharField(max_length=10, default='4-4-2')
    
    # Template players
    players = models.JSONField(default=list, help_text="List of player data for template")
    
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.team.team.name} ({self.formation})"
