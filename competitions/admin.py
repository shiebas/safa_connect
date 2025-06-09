from django.contrib import admin
from django.utils.html import format_html
from .models import Competition, Team, CompetitionTeam, Fixture, MatchEvent

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'competition_type', 'level', 'season_year', 'sponsor_display', 'is_active', 'team_count']
    list_filter = ['competition_type', 'level', 'season_year', 'is_active']
    search_fields = ['name', 'sponsor_name', 'safa_id']
    readonly_fields = ['safa_id', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ('name', 'short_name', 'competition_type', 'level', 'safa_id')
        }),
        ('Geography', {
            'fields': ('region', 'lfa')
        }),
        ('Season', {
            'fields': ('season_year', 'start_date', 'end_date')
        }),
        ('Sponsor', {
            'fields': ('sponsor_name', 'sponsor_logo')
        }),
        ('Settings', {
            'fields': ('max_teams', 'rounds', 'points_win', 'points_draw', 'points_loss')
        }),
        ('Status', {
            'fields': ('is_active', 'registration_open', 'fixtures_generated')
        }),
    ]
    
    def sponsor_display(self, obj):
        if obj.sponsor_logo:
            return format_html('<img src="{}" width="30" height="30" /> {}', 
                             obj.sponsor_logo.url, obj.sponsor_name or 'Sponsored')
        return obj.sponsor_name or '-'
    sponsor_display.short_description = 'Sponsor'
    
    def team_count(self, obj):
        return obj.teams.count()
    team_count.short_description = 'Teams'

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'lfa', 'manager_name', 'is_active']
    list_filter = ['lfa__region__province', 'lfa__region', 'is_active']
    search_fields = ['name', 'short_name', 'manager_name', 'safa_id']
    readonly_fields = ['safa_id', 'created_at', 'updated_at']

@admin.register(CompetitionTeam)
class CompetitionTeamAdmin(admin.ModelAdmin):
    list_display = ['team', 'competition', 'points', 'played', 'won', 'drawn', 'lost', 'goal_difference']
    list_filter = ['competition', 'registration_fee_paid']
    ordering = ['-points', '-goals_for']

@admin.register(Fixture)
class FixtureAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'competition', 'scheduled_date', 'status', 'score_display']
    list_filter = ['competition', 'status', 'scheduled_date']
    search_fields = ['home_team__team__name', 'away_team__team__name']
    
    def score_display(self, obj):
        if obj.status == 'completed' and obj.home_score is not None:
            return f"{obj.home_score} - {obj.away_score}"
        return '-'
    score_display.short_description = 'Score'

@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ['fixture', 'team', 'player_name', 'event_type', 'minute']
    list_filter = ['event_type', 'fixture__competition']
    search_fields = ['player_name', 'fixture__home_team__team__name', 'fixture__away_team__team__name']
