from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count, F
from .models import (
    Competition, CompetitionTeam, Match, PlayerStatistics, MatchEvent,
    TeamSheet, TeamSheetPlayer, PlayerDiscipline, ActivityLog, TeamSheetTemplate
)
import json

@staff_member_required
def team_sheet_list(request, competition_id):
    """List all team sheets for a competition"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Get upcoming matches with team sheets
    upcoming_matches = Match.objects.filter(
        competition=competition,
        status='scheduled'
    ).select_related('home_team', 'away_team').prefetch_related('team_sheets')
    
    # Get recent team sheets
    recent_sheets = TeamSheet.objects.filter(
        match__competition=competition
    ).select_related('match', 'team', 'submitted_by').order_by('-created_at')[:10]
    
    context = {
        'competition': competition,
        'upcoming_matches': upcoming_matches,
        'recent_sheets': recent_sheets,
    }
    
    return render(request, 'league_management/team_sheet_list.html', context)

@staff_member_required
def team_sheet_detail(request, match_id, team_id):
    """View team sheet details (read-only for opponents)"""
    match = get_object_or_404(Match, id=match_id)
    team = get_object_or_404(CompetitionTeam, id=team_id)
    
    try:
        team_sheet = TeamSheet.objects.get(match=match, team=team)
        players = team_sheet.players.all().order_by('jersey_number')
    except TeamSheet.DoesNotExist:
        team_sheet = None
        players = []
    
    # Check if user can edit (only team officials or staff)
    can_edit = (
        request.user.is_staff or 
        request.user.role in ['ADMIN_COUNTRY', 'ADMIN_PROVINCE', 'ADMIN_REGION'] or
        # Add logic to check if user is team official
        False
    )
    
    context = {
        'match': match,
        'team': team,
        'team_sheet': team_sheet,
        'players': players,
        'can_edit': can_edit,
    }
    
    return render(request, 'league_management/team_sheet_detail.html', context)

@staff_member_required
def team_sheet_create(request, match_id, team_id):
    """Create or edit team sheet"""
    match = get_object_or_404(Match, id=match_id)
    team = get_object_or_404(CompetitionTeam, id=team_id)
    
    # Get or create team sheet
    team_sheet, created = TeamSheet.objects.get_or_create(
        match=match,
        team=team,
        defaults={'status': 'draft'}
    )
    
    # Get available players with discipline status
    available_players = PlayerStatistics.objects.filter(
        competition=match.competition,
        team=team
    ).select_related().order_by('jersey_number')
    
    # Check player eligibility
    for player in available_players:
        discipline, _ = PlayerDiscipline.objects.get_or_create(
            competition=match.competition,
            team=team,
            player_name=player.player_name
        )
        player.is_eligible = discipline.is_eligible_for_selection
        player.suspension_reason = discipline.suspension_reason if not player.is_eligible else ""
    
    # Get existing team sheet players
    selected_players = {p.player_name: p for p in team_sheet.players.all()}
    
    # Get team sheet templates
    templates = TeamSheetTemplate.objects.filter(team=team).order_by('-created_at')
    
    if request.method == 'POST':
        with transaction.atomic():
            # Clear existing players
            team_sheet.players.all().delete()
            
            # Process form data
            players_data = json.loads(request.POST.get('players_data', '[]'))
            
            for player_data in players_data:
                TeamSheetPlayer.objects.create(
                    team_sheet=team_sheet,
                    player_name=player_data['name'],
                    jersey_number=player_data['jersey_number'],
                    position=player_data['position'],
                    is_starting=player_data.get('is_starting', True),
                    is_captain=player_data.get('is_captain', False),
                    is_vice_captain=player_data.get('is_vice_captain', False),
                    is_eligible=player_data.get('is_eligible', True),
                    suspension_reason=player_data.get('suspension_reason', '')
                )
            
            # Update team sheet
            team_sheet.formation = request.POST.get('formation', '4-4-2')
            team_sheet.captain = request.POST.get('captain', '')
            team_sheet.vice_captain = request.POST.get('vice_captain', '')
            team_sheet.notes = request.POST.get('notes', '')
            
            if request.POST.get('action') == 'submit':
                team_sheet.status = 'submitted'
                team_sheet.submitted_by = request.user
                team_sheet.submitted_at = timezone.now()
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action_type='team_sheet_submitted',
                    competition=match.competition,
                    match=match,
                    team=team,
                    description=f"Team sheet submitted for {team.team.name}",
                    details={'formation': team_sheet.formation, 'player_count': len(players_data)}
                )
                
                messages.success(request, 'Team sheet submitted successfully!')
            else:
                team_sheet.status = 'draft'
                messages.success(request, 'Team sheet saved as draft!')
            
            team_sheet.save()
            
            return redirect('league_management:team_sheet_detail', match_id=match.id, team_id=team.id)
    
    context = {
        'match': match,
        'team': team,
        'team_sheet': team_sheet,
        'available_players': available_players,
        'selected_players': selected_players,
        'templates': templates,
    }
    
    return render(request, 'league_management/team_sheet_create.html', context)

@staff_member_required
def team_sheet_from_template(request, match_id, team_id, template_id):
    """Create team sheet from template"""
    match = get_object_or_404(Match, id=match_id)
    team = get_object_or_404(CompetitionTeam, id=team_id)
    template = get_object_or_404(TeamSheetTemplate, id=template_id, team=team)
    
    # Get or create team sheet
    team_sheet, created = TeamSheet.objects.get_or_create(
        match=match,
        team=team,
        defaults={'status': 'draft'}
    )
    
    with transaction.atomic():
        # Clear existing players
        team_sheet.players.all().delete()
        
        # Create players from template
        for player_data in template.players:
            # Check if player is still available and eligible
            try:
                player_stat = PlayerStatistics.objects.get(
                    competition=match.competition,
                    team=team,
                    player_name=player_data['name']
                )
                
                discipline, _ = PlayerDiscipline.objects.get_or_create(
                    competition=match.competition,
                    team=team,
                    player_name=player_data['name']
                )
                
                TeamSheetPlayer.objects.create(
                    team_sheet=team_sheet,
                    player_name=player_data['name'],
                    jersey_number=player_data['jersey_number'],
                    position=player_data['position'],
                    is_starting=player_data.get('is_starting', True),
                    is_captain=player_data.get('is_captain', False),
                    is_vice_captain=player_data.get('is_vice_captain', False),
                    is_eligible=discipline.is_eligible_for_selection,
                    suspension_reason=discipline.suspension_reason if not discipline.is_eligible_for_selection else ''
                )
            except PlayerStatistics.DoesNotExist:
                # Player no longer in squad, skip
                continue
        
        # Update team sheet with template data
        team_sheet.formation = template.formation
        team_sheet.status = 'draft'
        team_sheet.save()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action_type='team_sheet_created',
            competition=match.competition,
            match=match,
            team=team,
            description=f"Team sheet created from template '{template.name}'",
            details={'template_id': str(template.id)}
        )
    
    messages.success(request, f'Team sheet created from template "{template.name}"!')
    return redirect('league_management:team_sheet_create', match_id=match.id, team_id=team.id)

@staff_member_required
def team_sheet_template_save(request, match_id, team_id):
    """Save current team sheet as template"""
    match = get_object_or_404(Match, id=match_id)
    team = get_object_or_404(CompetitionTeam, id=team_id)
    
    try:
        team_sheet = TeamSheet.objects.get(match=match, team=team)
    except TeamSheet.DoesNotExist:
        messages.error(request, 'No team sheet found to save as template!')
        return redirect('league_management:team_sheet_create', match_id=match.id, team_id=team.id)
    
    if request.method == 'POST':
        template_name = request.POST.get('template_name')
        if not template_name:
            messages.error(request, 'Template name is required!')
            return redirect('league_management:team_sheet_create', match_id=match.id, team_id=team.id)
        
        # Create template data
        players_data = []
        for player in team_sheet.players.all():
            players_data.append({
                'name': player.player_name,
                'jersey_number': player.jersey_number,
                'position': player.position,
                'is_starting': player.is_starting,
                'is_captain': player.is_captain,
                'is_vice_captain': player.is_vice_captain,
            })
        
        # Create template
        template = TeamSheetTemplate.objects.create(
            name=template_name,
            team=team,
            formation=team_sheet.formation,
            players=players_data,
            created_by=request.user
        )
        
        messages.success(request, f'Template "{template_name}" saved successfully!')
    
    return redirect('league_management:team_sheet_create', match_id=match.id, team_id=team.id)

@staff_member_required
def player_discipline_list(request, competition_id):
    """List all player discipline records for a competition"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Get discipline records
    discipline_records = PlayerDiscipline.objects.filter(
        competition=competition
    ).select_related('team').order_by('-total_red_cards', '-total_yellow_cards', 'player_name')
    
    # Pagination
    paginator = Paginator(discipline_records, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'competition': competition,
        'page_obj': page_obj,
    }
    
    return render(request, 'league_management/player_discipline_list.html', context)

@staff_member_required
def activity_logs(request, competition_id=None):
    """View activity logs for the system"""
    logs = ActivityLog.objects.select_related('user', 'competition', 'match', 'team').order_by('-timestamp')
    
    # Filter by competition if specified
    if competition_id:
        competition = get_object_or_404(Competition, id=competition_id)
        logs = logs.filter(competition=competition)
    else:
        competition = None
    
    # Filter by action type if specified
    action_type = request.GET.get('action_type')
    if action_type:
        logs = logs.filter(action_type=action_type)
    
    # Pagination
    paginator = Paginator(logs, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'competition': competition,
        'page_obj': page_obj,
        'action_types': ActivityLog.ACTION_TYPES,
        'selected_action_type': action_type,
    }
    
    return render(request, 'league_management/activity_logs.html', context)

@staff_member_required
def add_match_event(request, match_id):
    """Add match event (goals, cards, etc.)"""
    match = get_object_or_404(Match, id=match_id)
    
    if request.method == 'POST':
        event_type = request.POST.get('event_type')
        minute = request.POST.get('minute')
        player_name = request.POST.get('player_name')
        team_id = request.POST.get('team_id')
        description = request.POST.get('description', '')
        
        try:
            team = CompetitionTeam.objects.get(id=team_id)
            
            # Create match event
            event = MatchEvent.objects.create(
                match=match,
                team=team,
                event_type=event_type,
                minute=int(minute),
                player_name=player_name,
                description=description,
                recorded_by=request.user
            )
            
            # Update player discipline if it's a card
            if event_type in ['yellow_card', 'red_card', 'second_yellow']:
                discipline, _ = PlayerDiscipline.objects.get_or_create(
                    competition=match.competition,
                    team=team,
                    player_name=player_name
                )
                discipline.add_card(event_type)
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action_type='match_event_added',
                competition=match.competition,
                match=match,
                team=team,
                description=f"Added {event.get_event_type_display()} for {player_name}",
                details={'event_type': event_type, 'minute': minute}
            )
            
            return JsonResponse({'success': True, 'message': 'Event added successfully!'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    # Get teams for the match
    teams = [match.home_team, match.away_team]
    
    context = {
        'match': match,
        'teams': teams,
    }
    
    return render(request, 'league_management/add_match_event.html', context)
