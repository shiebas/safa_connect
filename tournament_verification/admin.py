from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import TournamentRegistration, VerificationLog
from .tournament_models import (
    SportCode, TournamentPlayer, TournamentCompetition, 
    TournamentTeam, TournamentTeamPlayer, TournamentPool, 
    TournamentMatch, TournamentStandings
)


@admin.register(TournamentRegistration)
class TournamentRegistrationAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'tournament', 'email', 'id_number', 'registration_type', 'verification_status_badge', 'verification_confidence', 'registered_at']
    list_filter = ['verification_status', 'registration_type', 'tournament', 'registered_at']
    search_fields = ['first_name', 'last_name', 'email', 'id_number', 'tournament__name']
    date_hierarchy = 'registered_at'
    ordering = ['-registered_at']
    readonly_fields = ['id', 'registered_at', 'verified_at', 'verification_score']
    
    fieldsets = (
        ('Registration Information', {
            'fields': ('id', 'tournament', 'registration_type', 'registered_at')
        }),
        ('Player Details', {
            'fields': ('player', 'first_name', 'last_name', 'email', 'phone_number', 'id_number')
        }),
        ('Photo Verification', {
            'fields': ('live_photo', 'stored_photo', 'verification_score', 'verification_status', 'verification_notes')
        }),
        ('Verification Details', {
            'fields': ('verified_at', 'verified_by'),
            'classes': ('collapse',)
        }),
    )
    
    def verification_status_badge(self, obj):
        colors = {
            'VERIFIED': 'green',
            'PENDING': 'orange',
            'FAILED': 'red',
            'MANUAL_REVIEW': 'blue',
            'REJECTED': 'darkred'
        }
        color = colors.get(obj.verification_status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_verification_status_display()
        )
    verification_status_badge.short_description = 'Status'
    
    def verification_confidence(self, obj):
        if obj.verification_confidence_percentage:
            color = 'green' if obj.verification_confidence_percentage >= 80 else 'orange' if obj.verification_confidence_percentage >= 60 else 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}%</span>',
                color,
                obj.verification_confidence_percentage
            )
        return 'N/A'
    verification_confidence.short_description = 'Confidence'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tournament', 'player', 'verified_by')

@admin.register(VerificationLog)
class VerificationLogAdmin(admin.ModelAdmin):
    list_display = ['registration', 'attempt_number', 'verification_status', 'verification_score', 'processed_by', 'created_at']
    list_filter = ['verification_status', 'created_at', 'processed_by']
    search_fields = ['registration__first_name', 'registration__last_name', 'registration__tournament__name']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Verification Details', {
            'fields': ('id', 'registration', 'attempt_number', 'verification_score', 'verification_status')
        }),
        ('Processing', {
            'fields': ('processed_by', 'created_at')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('registration__tournament', 'processed_by')

# New tournament models
@admin.register(SportCode)
class SportCodeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'players_per_team', 'match_duration_minutes', 'is_active']
    list_filter = ['is_active', 'code']
    search_fields = ['name', 'code', 'description']

@admin.register(TournamentPlayer)
class TournamentPlayerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone_number', 'date_of_birth', 'registration_date', 'is_active']
    list_filter = ['is_active', 'gender', 'registration_date']
    search_fields = ['first_name', 'last_name', 'email', 'id_number']
    date_hierarchy = 'registration_date'

@admin.register(TournamentCompetition)
class TournamentCompetitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'sport_code', 'tournament_type', 'start_date', 'location', 'is_active', 'is_published']
    list_filter = ['sport_code', 'tournament_type', 'is_active', 'is_published', 'start_date']
    search_fields = ['name', 'location', 'description']
    date_hierarchy = 'start_date'

@admin.register(TournamentTeam)
class TournamentTeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'tournament', 'pool', 'captain_name', 'is_confirmed', 'registration_date']
    list_filter = ['tournament', 'is_confirmed', 'registration_date']
    search_fields = ['name', 'captain_name', 'captain_email']

@admin.register(TournamentTeamPlayer)
class TournamentTeamPlayerAdmin(admin.ModelAdmin):
    list_display = ['player', 'team', 'position', 'jersey_number', 'is_captain', 'is_vice_captain']
    list_filter = ['team__tournament', 'position', 'is_captain', 'is_vice_captain']
    search_fields = ['player__first_name', 'player__last_name', 'team__name']

@admin.register(TournamentPool)
class TournamentPoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'tournament']
    list_filter = ['tournament']
    search_fields = ['name', 'tournament__name']

@admin.register(TournamentMatch)
class TournamentMatchAdmin(admin.ModelAdmin):
    list_display = ['home_team', 'away_team', 'tournament', 'match_date', 'status', 'round_name']
    list_filter = ['tournament', 'status', 'round_name', 'pool', 'match_date']
    search_fields = ['home_team__name', 'away_team__name', 'tournament__name']
    date_hierarchy = 'match_date'

@admin.register(TournamentStandings)
class TournamentStandingsAdmin(admin.ModelAdmin):
    list_display = ['team', 'tournament', 'pool', 'position', 'points', 'matches_played', 'goal_difference']
    list_filter = ['tournament', 'pool']
    search_fields = ['team__name', 'tournament__name']
    ordering = ['tournament', 'pool', 'position']
