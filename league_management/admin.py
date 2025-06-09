from django.contrib import admin
from django.utils.html import format_html
from .models import CompetitionCategory, Competition, CompetitionGroup, Team, CompetitionTeam, Match, MatchEvent

@admin.register(CompetitionCategory)
class CompetitionCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'level', 'gender', 'age_category', 'is_active']
    list_filter = ['level', 'gender', 'age_category', 'is_active']
    search_fields = ['name', 'short_name']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ('name', 'short_name', 'description')
        }),
        ('Classification', {
            'fields': ('level', 'gender', 'age_category')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    ]

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'region', 'season_year', 'team_count', 'sponsor_display', 'is_active']
    list_filter = ['category', 'region__province', 'season_year', 'is_active', 'has_groups']
    search_fields = ['name', 'safa_id', 'main_sponsor']
    readonly_fields = ['safa_id', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ('category', 'name', 'season_year', 'safa_id')
        }),
        ('Geography', {
            'fields': ('region',)
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Sponsor', {
            'fields': ('main_sponsor', 'sponsor_logo')
        }),
        ('Structure', {
            'fields': ('has_groups', 'teams_per_group')
        }),
        ('Points System', {
            'fields': ('points_win', 'points_draw', 'points_loss')
        }),
        ('Status', {
            'fields': ('is_active', 'registration_open')
        }),
    ]
    
    def sponsor_display(self, obj):
        if obj.sponsor_logo:
            return format_html('<img src="{}" width="30" height="30" /> {}', 
                             obj.sponsor_logo.url, obj.main_sponsor or 'Sponsored')
        return obj.main_sponsor or '-'
    sponsor_display.short_description = 'Sponsor'
    
    def team_count(self, obj):
        return obj.teams.count()
    team_count.short_description = 'Teams'

@admin.register(CompetitionGroup)
class CompetitionGroupAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'competition', 'group_type', 'team_count', 'max_teams']
    list_filter = ['competition__category', 'group_type']
    search_fields = ['name', 'competition__name']
    
    def team_count(self, obj):
        return obj.teams.count()
    team_count.short_description = 'Teams'

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'lfa', 'manager_name', 'is_active']
    list_filter = ['lfa__region__province', 'lfa__region', 'is_active', 'founded_year']
    search_fields = ['name', 'short_name', 'nickname', 'safa_id', 'manager_name']
    readonly_fields = ['safa_id', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ('name', 'short_name', 'nickname', 'safa_id')
        }),
        ('Geography', {
            'fields': ('lfa', 'home_ground')
        }),
        ('Management', {
            'fields': ('manager_name', 'coach_name', 'contact_person', 'contact_phone', 'contact_email')
        }),
        ('Appearance', {
            'fields': ('primary_color', 'secondary_color', 'team_logo')
        }),
        ('Details', {
            'fields': ('founded_year', 'is_active')
        }),
    ]

@admin.register(CompetitionTeam)
class CompetitionTeamAdmin(admin.ModelAdmin):
    list_display = ['team', 'competition', 'group', 'position', 'points', 'played', 'goal_difference']
    list_filter = ['competition', 'group', 'registration_fee_paid']
    search_fields = ['team__name', 'competition__name']
    ordering = ['-points', '-goals_for']
    
    def position(self, obj):
        return obj.league_position
    position.short_description = 'Pos'

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'competition', 'group', 'match_date', 'status', 'score_display']
    list_filter = ['competition', 'group', 'status', 'match_date']
    search_fields = ['home_team__team__name', 'away_team__team__name']
    date_hierarchy = 'match_date'
    
    fieldsets = [
        ('Match Details', {
            'fields': ('competition', 'group', 'home_team', 'away_team')
        }),
        ('Scheduling', {
            'fields': ('match_date', 'kickoff_time', 'venue')
        }),
        ('Results', {
            'fields': ('status', 'home_score', 'away_score')
        }),
        ('Officials', {
            'fields': ('referee', 'assistant_ref_1', 'assistant_ref_2', 'fourth_official')
        }),
        ('Additional Info', {
            'fields': ('attendance', 'weather_conditions', 'pitch_conditions')
        }),
    ]
    
    def score_display(self, obj):
        if obj.status == 'completed' and obj.home_score is not None:
            return f"{obj.home_score} - {obj.away_score}"
        return '-'
    score_display.short_description = 'Score'

@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ['match', 'minute', 'event_type', 'player_name', 'team']
    list_filter = ['event_type', 'match__competition']
    search_fields = ['player_name', 'match__home_team__team__name', 'match__away_team__team__name']
    ordering = ['match', 'minute']
