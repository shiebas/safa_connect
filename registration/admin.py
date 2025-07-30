from django.contrib import admin
from .models import Player, Official, PlayerClubRegistration


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'email', 'safa_id', 'status', 'has_active_club')
    list_filter = ('status', 'gender')
    search_fields = ('first_name', 'last_name', 'email', 'safa_id')
    
    def has_active_club(self, obj):
        return PlayerClubRegistration.objects.filter(player=obj, status='ACTIVE').exists()
    has_active_club.boolean = True
    has_active_club.short_description = 'Active Club'

@admin.register(Official)
class OfficialAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'email', 'safa_id', 'status')
    list_filter = ('status',)
    search_fields = ('first_name', 'last_name', 'email', 'safa_id')

@admin.register(PlayerClubRegistration)
class PlayerClubRegistrationAdmin(admin.ModelAdmin):
    list_display = ('player', 'club', 'status', 'registration_date', 'position')
    list_filter = ('status', 'registration_date')
    search_fields = ('player__first_name', 'player__last_name', 'club__name')