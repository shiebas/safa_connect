from django.contrib import admin
from .models import SupporterProfile

@admin.register(SupporterProfile)
class SupporterProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'favorite_club', 'membership_type', 'created_at']
    list_filter = ['membership_type', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
