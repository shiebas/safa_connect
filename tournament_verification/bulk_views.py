"""
Bulk management views for tournament system
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

from .models import TournamentRegistration
from .tournament_models import TournamentCompetition, TournamentTeam


@login_required
def bulk_management(request):
    """Bulk management page for tournaments, teams, and registrations"""
    if not request.user.is_superuser:
        return render(request, 'tournament_verification/error.html', {
            'error_message': 'Access denied. Superuser privileges required.'
        })
    
    # Get statistics
    total_tournaments = TournamentCompetition.objects.count()
    total_teams = TournamentTeam.objects.count()
    total_registrations = TournamentRegistration.objects.count()
    pending_verifications = TournamentRegistration.objects.filter(
        verification_status='PENDING'
    ).count()
    
    # Get data for each tab
    tournaments = TournamentCompetition.objects.all().order_by('-created_at')[:50]
    teams = TournamentTeam.objects.select_related('tournament').all().order_by('-registration_date')[:50]
    registrations = TournamentRegistration.objects.select_related(
        'tournament', 'team'
    ).all().order_by('-registered_at')[:50]
    
    context = {
        'total_tournaments': total_tournaments,
        'total_teams': total_teams,
        'total_registrations': total_registrations,
        'pending_verifications': pending_verifications,
        'tournaments': tournaments,
        'teams': teams,
        'registrations': registrations,
        'title': 'Bulk Management'
    }
    
    return render(request, 'tournament_verification/bulk_management.html', context)
