from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Count, Sum, Avg, Q, F
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from rest_framework import viewsets
from .models import Competition, CompetitionGroup, CompetitionTeam, Match, PlayerStatistics, LeagueTable, CompetitionCategory
from .serializers import CompetitionCategorySerializer, CompetitionSerializer

@staff_member_required
def dashboard(request):
    """Main admin dashboard for league management"""
    # Overview statistics
    total_competitions = Competition.objects.filter(is_active=True).count()
    total_teams = CompetitionTeam.objects.count()
    total_matches = Match.objects.count()
    completed_matches = Match.objects.filter(status='completed').count()
    
    # Recent competitions
    recent_competitions = Competition.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    # Upcoming matches
    upcoming_matches = Match.objects.filter(
        status='scheduled'
    ).order_by('match_date')[:10]
    
    # Active competitions by category
    competition_stats = Competition.objects.filter(is_active=True).values(
        'category__name'
    ).annotate(
        count=Count('id'),
        total_teams=Count('teams')
    ).order_by('-count')
    
    context = {
        'total_competitions': total_competitions,
        'total_teams': total_teams,
        'total_matches': total_matches,
        'completed_matches': completed_matches,
        'recent_competitions': recent_competitions,
        'upcoming_matches': upcoming_matches,
        'competition_stats': competition_stats,
    }
    
    return render(request, 'league_management/dashboard.html', context)

@staff_member_required
def competition_detail(request, competition_id):
    """Detailed view of a specific competition"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Competition statistics
    teams = competition.teams.all()
    matches = competition.matches.all()
    completed_matches = matches.filter(status='completed')
    
    # League table
    league_table = teams.order_by('-points', '-goals_for', 'goals_against')
    
    # Recent matches
    recent_matches = completed_matches.order_by('-match_date')[:5]
    
    # Top scorers
    top_scorers = PlayerStatistics.objects.filter(
        competition=competition
    ).order_by('-goals')[:5]
    
    context = {
        'competition': competition,
        'teams': teams,
        'matches': matches,
        'completed_matches': completed_matches,
        'league_table': league_table,
        'recent_matches': recent_matches,
        'top_scorers': top_scorers,
    }
    
    return render(request, 'league_management/competition_detail.html', context)

def league_statistics(request, competition_id, group_id=None):
    """Generate comprehensive league statistics like inqaku.com"""
    competition = get_object_or_404(Competition, id=competition_id)
    group = None
    if group_id:
        group = get_object_or_404(CompetitionGroup, id=group_id)
    
    # Filter teams and matches
    if group:
        teams = group.teams.all()
        matches = group.matches.all()
    else:
        teams = competition.teams.all()
        matches = competition.matches.all()
    
    # League Table
    league_table = teams.order_by('-points', '-goals_for', 'goals_against')
    
    # Top Scorers
    top_scorers = PlayerStatistics.objects.filter(
        competition=competition,
        team__in=teams
    ).order_by('-goals', '-assists')[:10]
    
    # Team Statistics
    team_stats = []
    for team in teams:
        team_matches = matches.filter(Q(home_team=team) | Q(away_team=team))
        home_matches = team_matches.filter(home_team=team, status='completed')
        away_matches = team_matches.filter(away_team=team, status='completed')
        
        # Calculate detailed stats
        total_goals_for = team.goals_for
        total_goals_against = team.goals_against
        home_goals_for = sum([m.home_score or 0 for m in home_matches])
        away_goals_for = sum([m.away_score or 0 for m in away_matches])
        
        team_stats.append({
            'team': team,
            'total_matches': team.played,
            'home_matches': home_matches.count(),
            'away_matches': away_matches.count(),
            'goals_for': total_goals_for,
            'goals_against': total_goals_against,
            'goal_difference': total_goals_for - total_goals_against,
            'home_goals_for': home_goals_for,
            'away_goals_for': away_goals_for,
            'avg_goals_per_match': round(total_goals_for / max(team.played, 1), 2),
            'clean_sheets': PlayerStatistics.objects.filter(
                team=team, 
                position='GK'
            ).aggregate(total=Sum('clean_sheets'))['total'] or 0
        })
    
    # Match Statistics
    completed_matches = matches.filter(status='completed')
    total_goals = sum([
        (match.home_score or 0) + (match.away_score or 0) 
        for match in completed_matches
    ])
    
    match_stats = {
        'total_matches': completed_matches.count(),
        'total_goals': total_goals,
        'avg_goals_per_match': round(total_goals / max(completed_matches.count(), 1), 2),
        'home_wins': completed_matches.filter(home_score__gt=F('away_score')).count(),
        'away_wins': completed_matches.filter(away_score__gt=F('home_score')).count(),
        'draws': completed_matches.filter(home_score=F('away_score')).count(),
    }
    
    # Recent Matches
    recent_matches = matches.filter(status='completed').order_by('-match_date')[:10]
    
    # Upcoming Matches  
    upcoming_matches = matches.filter(status='scheduled').order_by('match_date')[:10]
    
    context = {
        'competition': competition,
        'group': group,
        'league_table': league_table,
        'top_scorers': top_scorers,
        'team_stats': team_stats,
        'match_stats': match_stats,
        'recent_matches': recent_matches,
        'upcoming_matches': upcoming_matches,
    }
    
    return render(request, 'league_management/statistics.html', context)

def team_statistics(request, competition_id, team_id):
    """Detailed statistics for a specific team"""
    competition = get_object_or_404(Competition, id=competition_id)
    team = get_object_or_404(CompetitionTeam, id=team_id, competition=competition)
    
    # Player statistics for this team
    players = PlayerStatistics.objects.filter(team=team).order_by('-goals')
    
    # Match history
    matches = Match.objects.filter(
        Q(home_team=team) | Q(away_team=team),
        competition=competition
    ).order_by('-match_date')
    
    # Form calculation (last 5 matches)
    recent_matches = matches.filter(status='completed')[:5]
    form = []
    for match in recent_matches:
        if match.home_team == team:
            if match.home_score > match.away_score:
                form.append('W')
            elif match.home_score < match.away_score:
                form.append('L')
            else:
                form.append('D')
        else:
            if match.away_score > match.home_score:
                form.append('W')
            elif match.away_score < match.home_score:
                form.append('L')
            else:
                form.append('D')
    
    context = {
        'competition': competition,
        'team': team,
        'players': players,
        'matches': matches,
        'form': ''.join(form),
    }
    
    return render(request, 'league_management/team_statistics.html', context)

class CompetitionCategoryViewSet(viewsets.ModelViewSet):
    queryset = CompetitionCategory.objects.all()
    serializer_class = CompetitionCategorySerializer

from django.core.management import call_command
from io import StringIO

class CompetitionViewSet(viewsets.ModelViewSet):
    queryset = Competition.objects.all()
    serializer_class = CompetitionSerializer

@staff_member_required
def fixture_generation_view(request):
    competitions = Competition.objects.all().order_by('name')
    groups = CompetitionGroup.objects.all().order_by('name')
    
    if request.method == 'POST':
        competition_id = request.POST.get('competition')
        group_id = request.POST.get('group')
        clear_existing = request.POST.get('clear_existing') == 'on'
        
        if not competition_id:
            messages.error(request, "Please select a competition.")
            return redirect('league_management:fixture_generation')
            
        args = [competition_id]
        options = {'clear_existing': clear_existing}
        
        if group_id:
            options['group_id'] = group_id
            
        out = StringIO()
        try:
            call_command('generate_fixtures', *args, stdout=out, **options)
            messages.success(request, f"Fixture generation initiated successfully. Output: {out.getvalue()}")
        except Exception as e:
            messages.error(request, f"Error generating fixtures: {e}. Output: {out.getvalue()}")
            
        return redirect('league_management:fixture_generation')
        
    context = {
        'competitions': competitions,
        'groups': groups,
    }
    return render(request, 'league_management/fixture_generation.html', context)
