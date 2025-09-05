"""
Tournament Fixture Generator

This module provides functionality to generate fixtures for different tournament formats:
- Round Robin (every team plays every other team)
- Knockout Tournament
- Pool Play + Playoffs
- League Format
"""

from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from django.utils import timezone
from .tournament_models import TournamentCompetition, TournamentTeam, TournamentFixture


class FixtureGenerator:
    """Generate fixtures for tournaments"""
    
    def __init__(self, tournament: TournamentCompetition):
        self.tournament = tournament
        self.teams = list(tournament.teams.all())
        self.match_duration = tournament.sport_code.match_duration_minutes if tournament.sport_code else 90
        self.break_between_matches = 30  # 30 minutes break between matches
    
    def generate_fixtures(self) -> List[TournamentFixture]:
        """Generate fixtures based on tournament type"""
        if not self.teams:
            return []
        
        # Clear existing fixtures
        self.tournament.fixtures.all().delete()
        
        if self.tournament.tournament_type == 'ROUND_ROBIN':
            return self._generate_round_robin()
        elif self.tournament.tournament_type == 'KNOCKOUT':
            return self._generate_knockout()
        elif self.tournament.tournament_type == 'POOL_PLAYOFF':
            return self._generate_pool_playoff()
        elif self.tournament.tournament_type == 'LEAGUE':
            return self._generate_league()
        else:
            # Default to round robin
            return self._generate_round_robin()
    
    def _generate_round_robin(self) -> List[TournamentFixture]:
        """Generate round robin fixtures (every team plays every other team)"""
        fixtures = []
        num_teams = len(self.teams)
        
        if num_teams < 2:
            return fixtures
        
        # Generate all possible matches
        matches = []
        for i in range(num_teams):
            for j in range(i + 1, num_teams):
                matches.append((self.teams[i], self.teams[j]))
        
        # Schedule matches
        current_time = self.tournament.start_date
        for home_team, away_team in matches:
            fixture = TournamentFixture(
                tournament=self.tournament,
                home_team=home_team,
                away_team=away_team,
                match_date=current_time,
                venue=self.tournament.location,
                round_name="Round Robin"
            )
            fixtures.append(fixture)
            
            # Move to next match time
            current_time += timedelta(minutes=self.match_duration + self.break_between_matches)
        
        return fixtures
    
    def _generate_knockout(self) -> List[TournamentFixture]:
        """Generate knockout tournament fixtures"""
        fixtures = []
        num_teams = len(self.teams)
        
        if num_teams < 2:
            return fixtures
        
        # Ensure we have a power of 2 teams for knockout
        # If not, we'll need to add byes or preliminary rounds
        current_teams = self.teams.copy()
        current_time = self.tournament.start_date
        round_num = 1
        
        while len(current_teams) > 1:
            round_name = self._get_round_name(len(current_teams))
            next_round_teams = []
            
            # Pair teams for this round
            for i in range(0, len(current_teams), 2):
                if i + 1 < len(current_teams):
                    home_team = current_teams[i]
                    away_team = current_teams[i + 1]
                    
                    fixture = TournamentFixture(
                        tournament=self.tournament,
                        home_team=home_team,
                        away_team=away_team,
                        match_date=current_time,
                        venue=self.tournament.location,
                        round_name=round_name
                    )
                    fixtures.append(fixture)
                    
                    # Add winner to next round (we'll update this when match is completed)
                    next_round_teams.append(home_team)  # Placeholder
                    
                    current_time += timedelta(minutes=self.match_duration + self.break_between_matches)
                else:
                    # Odd number of teams - this team gets a bye
                    next_round_teams.append(current_teams[i])
            
            current_teams = next_round_teams
            round_num += 1
        
        return fixtures
    
    def _generate_pool_playoff(self) -> List[TournamentFixture]:
        """Generate pool play + playoff fixtures"""
        fixtures = []
        num_teams = len(self.teams)
        
        if num_teams < 4:
            # Not enough teams for pool play, fall back to round robin
            return self._generate_round_robin()
        
        # Determine number of pools (typically 2-4 pools)
        if num_teams <= 6:
            num_pools = 2
        elif num_teams <= 8:
            num_pools = 2
        elif num_teams <= 12:
            num_pools = 3
        else:
            num_pools = 4
        
        teams_per_pool = num_teams // num_pools
        remaining_teams = num_teams % num_pools
        
        # Distribute teams into pools
        pools = []
        team_index = 0
        
        for pool_num in range(num_pools):
            pool_size = teams_per_pool + (1 if pool_num < remaining_teams else 0)
            pool_teams = self.teams[team_index:team_index + pool_size]
            pools.append(pool_teams)
            team_index += pool_size
        
        current_time = self.tournament.start_date
        
        # Generate pool play fixtures
        for pool_num, pool_teams in enumerate(pools):
            pool_name = f"Pool {chr(65 + pool_num)}"  # Pool A, Pool B, etc.
            
            # Round robin within each pool
            for i in range(len(pool_teams)):
                for j in range(i + 1, len(pool_teams)):
                    fixture = TournamentFixture(
                        tournament=self.tournament,
                        home_team=pool_teams[i],
                        away_team=pool_teams[j],
                        match_date=current_time,
                        venue=self.tournament.location,
                        pool=pool_name,
                        round_name="Pool Play"
                    )
                    fixtures.append(fixture)
                    current_time += timedelta(minutes=self.match_duration + self.break_between_matches)
        
        # Add playoff fixtures (semi-finals and final)
        # This is a simplified version - in reality, you'd need to determine
        # which teams advance based on pool standings
        
        return fixtures
    
    def _generate_league(self) -> List[TournamentFixture]:
        """Generate league format fixtures (home and away matches)"""
        fixtures = []
        num_teams = len(self.teams)
        
        if num_teams < 2:
            return fixtures
        
        current_time = self.tournament.start_date
        
        # First half of season (home matches)
        for i in range(num_teams):
            for j in range(num_teams):
                if i != j:
                    fixture = TournamentFixture(
                        tournament=self.tournament,
                        home_team=self.teams[i],
                        away_team=self.teams[j],
                        match_date=current_time,
                        venue=self.tournament.location,
                        round_name="League - First Half"
                    )
                    fixtures.append(fixture)
                    current_time += timedelta(minutes=self.match_duration + self.break_between_matches)
        
        # Second half of season (away matches)
        for i in range(num_teams):
            for j in range(num_teams):
                if i != j:
                    fixture = TournamentFixture(
                        tournament=self.tournament,
                        home_team=self.teams[j],  # Reversed for away matches
                        away_team=self.teams[i],
                        match_date=current_time,
                        venue=self.tournament.location,
                        round_name="League - Second Half"
                    )
                    fixtures.append(fixture)
                    current_time += timedelta(minutes=self.match_duration + self.break_between_matches)
        
        return fixtures
    
    def _get_round_name(self, num_teams: int) -> str:
        """Get appropriate round name based on number of teams"""
        if num_teams == 2:
            return "Final"
        elif num_teams == 4:
            return "Semi Final"
        elif num_teams == 8:
            return "Quarter Final"
        elif num_teams == 16:
            return "Round of 16"
        elif num_teams == 32:
            return "Round of 32"
        else:
            return f"Round of {num_teams}"
    
    def save_fixtures(self, fixtures: List[TournamentFixture]) -> List[TournamentFixture]:
        """Save fixtures to database"""
        saved_fixtures = []
        for fixture in fixtures:
            fixture.save()
            saved_fixtures.append(fixture)
        return saved_fixtures


def generate_tournament_fixtures(tournament_id: str) -> List[TournamentFixture]:
    """Generate fixtures for a tournament"""
    try:
        tournament = TournamentCompetition.objects.get(id=tournament_id)
        generator = FixtureGenerator(tournament)
        fixtures = generator.generate_fixtures()
        return generator.save_fixtures(fixtures)
    except TournamentCompetition.DoesNotExist:
        return []


def check_tournament_has_fixtures(tournament_id: str) -> bool:
    """Check if a tournament has fixtures generated"""
    try:
        tournament = TournamentCompetition.objects.get(id=tournament_id)
        return tournament.fixtures.exists()
    except TournamentCompetition.DoesNotExist:
        return False