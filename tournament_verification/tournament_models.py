from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
from django.utils import timezone

User = get_user_model()

# Sport Code Choices
SPORT_CODE_CHOICES = [
    ('SOCCER', 'Soccer/Football'),
    ('RUGBY', 'Rugby'),
    ('BASKETBALL', 'Basketball'),
    ('TENNIS', 'Tennis'),
    ('CRICKET', 'Cricket'),
    ('ATHLETICS', 'Athletics'),
    ('SWIMMING', 'Swimming'),
    ('OTHER', 'Other'),
]

# Tournament Types
TOURNAMENT_TYPE_CHOICES = [
    ('KNOCKOUT', 'Knockout Tournament'),
    ('ROUND_ROBIN', 'Round Robin'),
    ('POOL_PLAYOFF', 'Pool Play + Playoffs'),
    ('LEAGUE', 'League Format'),
]

# Match Status
MATCH_STATUS_CHOICES = [
    ('SCHEDULED', 'Scheduled'),
    ('IN_PROGRESS', 'In Progress'),
    ('COMPLETED', 'Completed'),
    ('POSTPONED', 'Postponed'),
    ('CANCELLED', 'Cancelled'),
]

class SportCode(models.Model):
    """Model for different sport codes with their specific rules"""
    code = models.CharField(max_length=20, choices=SPORT_CODE_CHOICES, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Sport-specific settings
    players_per_team = models.PositiveIntegerField(default=11, help_text="Default players per team")
    match_duration_minutes = models.PositiveIntegerField(default=90, help_text="Default match duration in minutes")
    has_extra_time = models.BooleanField(default=False)
    has_penalties = models.BooleanField(default=False)
    
    # Scoring system
    points_for_win = models.PositiveIntegerField(default=3)
    points_for_draw = models.PositiveIntegerField(default=1)
    points_for_loss = models.PositiveIntegerField(default=0)
    
    # Field/Court specifications
    field_length_min = models.PositiveIntegerField(default=90, help_text="Minimum field length in meters")
    field_length_max = models.PositiveIntegerField(default=120, help_text="Maximum field length in meters")
    field_width_min = models.PositiveIntegerField(default=45, help_text="Minimum field width in meters")
    field_width_max = models.PositiveIntegerField(default=90, help_text="Maximum field width in meters")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Sport Code"
        verbose_name_plural = "Sport Codes"
    
    def __str__(self):
        return self.name

class TournamentPlayer(models.Model):
    """Separate tournament player model - independent of SAFA system"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    
    # Identification
    id_number = models.CharField(max_length=20, help_text="ID Number or Passport")
    id_document_type = models.CharField(max_length=20, choices=[
        ('ID', 'National ID'),
        ('PASSPORT', 'Passport'),
        ('DRIVER_LICENSE', 'Driver License'),
        ('OTHER', 'Other'),
    ], default='ID')
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=200)
    emergency_contact_phone = models.CharField(max_length=20)
    emergency_contact_relationship = models.CharField(max_length=50)
    
    # Medical Information
    medical_conditions = models.TextField(blank=True, help_text="Any medical conditions or allergies")
    medical_aid_number = models.CharField(max_length=50, blank=True)
    
    # Photo for verification
    profile_photo = models.ImageField(upload_to='tournament_players/', null=True, blank=True)
    
    # Registration details
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, 
                                         help_text="Registration fee (R0.00 for tournament players)")
    registration_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Optional: Link to existing SAFA user (if they want to connect)
    safa_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 help_text="Optional link to existing SAFA user")
    
    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = "Tournament Player"
        verbose_name_plural = "Tournament Players"
        unique_together = ['id_number', 'email']  # Prevent duplicate registrations
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

class TournamentCompetition(models.Model):
    """Enhanced Tournament model with sport codes and pools"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Sport and Tournament Type
    sport_code = models.ForeignKey(SportCode, on_delete=models.CASCADE, related_name='tournaments')
    tournament_type = models.CharField(max_length=20, choices=TOURNAMENT_TYPE_CHOICES, default='POOL_PLAYOFF')
    
    # Dates and Location
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    registration_deadline = models.DateTimeField()
    location = models.CharField(max_length=200)
    venue_address = models.TextField(blank=True)
    
    # Tournament Settings
    max_teams = models.PositiveIntegerField(default=16)
    max_players_per_team = models.PositiveIntegerField(default=15)
    min_players_per_team = models.PositiveIntegerField(default=7)
    
    # Pool Settings (for pool-based tournaments)
    pool_size = models.PositiveIntegerField(default=4, help_text="Teams per pool")
    teams_advance_from_pool = models.PositiveIntegerField(default=2, help_text="Teams that advance from each pool")
    
    # Registration
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_registration_open = models.BooleanField(default=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    
    # Organizer
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_tournaments')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = "Tournament"
        verbose_name_plural = "Tournaments"
    
    def __str__(self):
        return f"{self.name} ({self.sport_code.name})"
    
    @property
    def is_registration_closed(self):
        return timezone.now() > self.registration_deadline
    
    @property
    def total_registered_teams(self):
        return self.teams.count()
    
    @property
    def can_register_teams(self):
        return (self.is_registration_open and 
                not self.is_registration_closed and 
                self.total_registered_teams < self.max_teams)

class TournamentTeam(models.Model):
    """Teams participating in tournaments"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(TournamentCompetition, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=10, help_text="Team abbreviation")
    
    # Team Details
    team_color_primary = models.CharField(max_length=7, default='#000000', help_text="Primary team color (hex)")
    team_color_secondary = models.CharField(max_length=7, default='#FFFFFF', help_text="Secondary team color (hex)")
    
    # Team Pictures for Visual Selection
    team_logo = models.ImageField(upload_to='tournament_teams/logos/', null=True, blank=True, 
                                 help_text="Team logo for visual selection")
    team_photo = models.ImageField(upload_to='tournament_teams/photos/', null=True, blank=True,
                                  help_text="Team photo for visual selection")
    
    # Contact Information
    captain_name = models.CharField(max_length=200)
    captain_phone = models.CharField(max_length=20)
    captain_email = models.EmailField()
    
    # Registration
    registration_date = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False)
    
    # Pool Assignment (for pool-based tournaments)
    pool = models.CharField(max_length=10, blank=True, help_text="Pool assignment (A, B, C, etc.)")
    
    class Meta:
        ordering = ['name']
        verbose_name = "Tournament Team"
        verbose_name_plural = "Tournament Teams"
        unique_together = ['tournament', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.tournament.name})"
    
    @property
    def total_players(self):
        return self.players.count()
    
    @property
    def is_complete(self):
        return (self.total_players >= self.tournament.min_players_per_team and 
                self.total_players <= self.tournament.max_players_per_team)
    
    def generate_team_photo(self):
        """Generate a composite team photo from player registrations"""
        from .team_photo_generator import team_photo_generator
        
        try:
            # Generate the composite team photo
            team_photo_file = team_photo_generator.generate_team_photo(self)
            
            if team_photo_file:
                # Save to team_photo field
                self.team_photo.save(
                    f"team_photo_{self.id}.jpg",
                    team_photo_file,
                    save=True
                )
                return True
        except Exception as e:
            print(f"Error generating team photo for {self.name}: {e}")
            return False
        
        return False
    
    def get_team_photo_url(self):
        """Get the team photo URL, generating one if needed"""
        if self.team_photo:
            return self.team_photo.url
        elif self.team_logo:
            return self.team_logo.url
        else:
            # Try to generate a team photo
            if self.generate_team_photo():
                return self.team_photo.url
            return None

class TournamentTeamPlayer(models.Model):
    """Players assigned to tournament teams"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(TournamentTeam, on_delete=models.CASCADE, related_name='players')
    player = models.ForeignKey(TournamentPlayer, on_delete=models.CASCADE, related_name='team_assignments')
    
    # Player Position/Role
    position = models.CharField(max_length=50, blank=True, help_text="Player position (e.g., Goalkeeper, Forward)")
    jersey_number = models.PositiveIntegerField(null=True, blank=True)
    is_captain = models.BooleanField(default=False)
    is_vice_captain = models.BooleanField(default=False)
    
    # Assignment details
    assigned_date = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['jersey_number', 'player__last_name']
        verbose_name = "Tournament Team Player"
        verbose_name_plural = "Tournament Team Players"
        unique_together = ['team', 'player']  # Player can only be in one team per tournament
        unique_together = ['team', 'jersey_number']  # Jersey numbers unique per team
    
    def __str__(self):
        return f"{self.player.full_name} - {self.team.name}"

class TournamentPool(models.Model):
    """Pools for pool-based tournaments"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(TournamentCompetition, on_delete=models.CASCADE, related_name='pools')
    name = models.CharField(max_length=10, help_text="Pool name (A, B, C, etc.)")
    teams = models.ManyToManyField(TournamentTeam, related_name='pool_assignments', blank=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Tournament Pool"
        verbose_name_plural = "Tournament Pools"
        unique_together = ['tournament', 'name']
    
    def __str__(self):
        return f"Pool {self.name} - {self.tournament.name}"

class TournamentMatch(models.Model):
    """Matches in tournaments"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(TournamentCompetition, on_delete=models.CASCADE, related_name='matches')
    
    # Teams
    home_team = models.ForeignKey(TournamentTeam, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(TournamentTeam, on_delete=models.CASCADE, related_name='away_matches')
    
    # Match Details
    match_date = models.DateTimeField()
    venue = models.CharField(max_length=200, blank=True)
    referee = models.CharField(max_length=200, blank=True)
    
    # Pool/Round Information
    pool = models.CharField(max_length=10, blank=True, help_text="Pool for pool matches")
    round_name = models.CharField(max_length=50, blank=True, help_text="Round name (e.g., 'Pool Play', 'Quarter Final')")
    match_number = models.PositiveIntegerField(default=1)
    
    # Match Status and Results
    status = models.CharField(max_length=20, choices=MATCH_STATUS_CHOICES, default='SCHEDULED')
    
    # Soccer/Football specific results
    home_score = models.PositiveIntegerField(default=0)
    away_score = models.PositiveIntegerField(default=0)
    home_score_extra_time = models.PositiveIntegerField(default=0, null=True, blank=True)
    away_score_extra_time = models.PositiveIntegerField(default=0, null=True, blank=True)
    home_penalties = models.PositiveIntegerField(default=0, null=True, blank=True)
    away_penalties = models.PositiveIntegerField(default=0, null=True, blank=True)
    
    # Rugby specific results
    home_tries = models.PositiveIntegerField(default=0, null=True, blank=True)
    away_tries = models.PositiveIntegerField(default=0, null=True, blank=True)
    home_conversions = models.PositiveIntegerField(default=0, null=True, blank=True)
    away_conversions = models.PositiveIntegerField(default=0, null=True, blank=True)
    home_penalties_rugby = models.PositiveIntegerField(default=0, null=True, blank=True)
    away_penalties_rugby = models.PositiveIntegerField(default=0, null=True, blank=True)
    home_drop_goals = models.PositiveIntegerField(default=0, null=True, blank=True)
    away_drop_goals = models.PositiveIntegerField(default=0, null=True, blank=True)
    
    # Match Notes
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['match_date', 'match_number']
        verbose_name = "Tournament Match"
        verbose_name_plural = "Tournament Matches"
    
    def __str__(self):
        return f"{self.home_team.name} vs {self.away_team.name} - {self.tournament.name}"
    
    @property
    def is_completed(self):
        return self.status == 'COMPLETED'
    
    @property
    def winner(self):
        if not self.is_completed:
            return None
        
        if self.tournament.sport_code.code == 'SOCCER':
            if self.home_score > self.away_score:
                return self.home_team
            elif self.away_score > self.home_score:
                return self.away_team
            else:
                return None  # Draw
        elif self.tournament.sport_code.code == 'RUGBY':
            home_total = self.home_score
            away_total = self.away_score
            if home_total > away_total:
                return self.home_team
            elif away_total > home_total:
                return self.away_team
            else:
                return None  # Draw
    
    @property
    def is_draw(self):
        if not self.is_completed:
            return False
        return self.winner is None

class TournamentStandings(models.Model):
    """Standings for teams in tournaments"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(TournamentCompetition, on_delete=models.CASCADE, related_name='standings')
    team = models.ForeignKey(TournamentTeam, on_delete=models.CASCADE, related_name='standings')
    pool = models.CharField(max_length=10, blank=True)
    
    # Match Statistics
    matches_played = models.PositiveIntegerField(default=0)
    matches_won = models.PositiveIntegerField(default=0)
    matches_drawn = models.PositiveIntegerField(default=0)
    matches_lost = models.PositiveIntegerField(default=0)
    
    # Goals/Points
    goals_for = models.PositiveIntegerField(default=0)
    goals_against = models.PositiveIntegerField(default=0)
    goal_difference = models.IntegerField(default=0)
    
    # Points
    points = models.PositiveIntegerField(default=0)
    
    # Position
    position = models.PositiveIntegerField(default=1)
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['pool', 'position', '-points', '-goal_difference']
        verbose_name = "Tournament Standing"
        verbose_name_plural = "Tournament Standings"
        unique_together = ['tournament', 'team']
    
    def __str__(self):
        return f"{self.team.name} - Position {self.position}"
    
    def calculate_goal_difference(self):
        self.goal_difference = self.goals_for - self.goals_against
        return self.goal_difference
    
    def calculate_points(self):
        if self.tournament.sport_code.code in ['SOCCER', 'RUGBY']:
            self.points = (self.matches_won * self.tournament.sport_code.points_for_win + 
                          self.matches_drawn * self.tournament.sport_code.points_for_draw + 
                          self.matches_lost * self.tournament.sport_code.points_for_loss)
        return self.points


class TournamentFixture(models.Model):
    """Model for tournament fixtures/matches"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(TournamentCompetition, on_delete=models.CASCADE, related_name='fixtures')
    
    # Teams
    home_team = models.ForeignKey(TournamentTeam, on_delete=models.CASCADE, related_name='home_fixtures')
    away_team = models.ForeignKey(TournamentTeam, on_delete=models.CASCADE, related_name='away_fixtures')
    
    # Match Details
    match_date = models.DateTimeField()
    venue = models.CharField(max_length=200, blank=True)
    pool = models.CharField(max_length=10, blank=True, help_text="Pool/Group name for pool play tournaments")
    round_name = models.CharField(max_length=50, blank=True, help_text="Round name (e.g., 'Quarter Final', 'Semi Final')")
    
    # Match Status
    status = models.CharField(max_length=20, choices=MATCH_STATUS_CHOICES, default='SCHEDULED')
    
    # Scores
    home_score = models.PositiveIntegerField(null=True, blank=True)
    away_score = models.PositiveIntegerField(null=True, blank=True)
    
    # Extra Time (for knockout matches)
    home_score_et = models.PositiveIntegerField(null=True, blank=True)
    away_score_et = models.PositiveIntegerField(null=True, blank=True)
    
    # Penalties (for knockout matches)
    home_penalties = models.PositiveIntegerField(null=True, blank=True)
    away_penalties = models.PositiveIntegerField(null=True, blank=True)
    
    # Match Officials
    referee = models.CharField(max_length=100, blank=True)
    assistant_referee_1 = models.CharField(max_length=100, blank=True)
    assistant_referee_2 = models.CharField(max_length=100, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['match_date', 'venue']
        verbose_name = "Tournament Fixture"
        verbose_name_plural = "Tournament Fixtures"
        unique_together = ['tournament', 'home_team', 'away_team', 'match_date']
    
    def __str__(self):
        return f"{self.home_team.name} vs {self.away_team.name} - {self.match_date.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def is_completed(self):
        return self.status == 'COMPLETED'
    
    @property
    def is_scheduled(self):
        return self.status == 'SCHEDULED'
    
    @property
    def is_in_progress(self):
        return self.status == 'IN_PROGRESS'
    
    @property
    def winner(self):
        """Determine the winner of the match"""
        if not self.is_completed:
            return None
        
        # Check penalties first (for knockout matches)
        if self.home_penalties is not None and self.away_penalties is not None:
            if self.home_penalties > self.away_penalties:
                return self.home_team
            elif self.away_penalties > self.home_penalties:
                return self.away_team
            else:
                return None  # Draw in penalties (shouldn't happen in knockout)
        
        # Check extra time scores
        if self.home_score_et is not None and self.away_score_et is not None:
            if self.home_score_et > self.away_score_et:
                return self.home_team
            elif self.away_score_et > self.home_score_et:
                return self.away_team
            else:
                return None  # Draw in extra time
        
        # Check regular time scores
        if self.home_score is not None and self.away_score is not None:
            if self.home_score > self.away_score:
                return self.home_team
            elif self.away_score > self.home_score:
                return self.away_team
            else:
                return None  # Draw
        
        return None
    
    @property
    def is_draw(self):
        """Check if the match was a draw"""
        if not self.is_completed:
            return False
        return self.winner is None
    
    def get_score_display(self):
        """Get formatted score display"""
        if not self.is_completed:
            return "vs"
        
        if self.home_penalties is not None and self.away_penalties is not None:
            return f"{self.home_score_et or self.home_score} ({self.home_penalties}) - {self.away_score_et or self.away_score} ({self.away_penalties})"
        elif self.home_score_et is not None and self.away_score_et is not None:
            return f"{self.home_score_et} (ET) - {self.away_score_et} (ET)"
        else:
            return f"{self.home_score} - {self.away_score}"
