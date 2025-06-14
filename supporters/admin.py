from django.contrib import admin
from .models import SupporterProfile

@admin.register(SupporterProfile)
class SupporterProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'favorite_club', 'membership_type', 'is_verified', 'created_at',
        'digital_card', 'physical_card', 'invoice'
    )
    list_filter = ('membership_type', 'is_verified', 'favorite_club')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'id_number')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('user', 'favorite_club', 'membership_type', 'is_verified', 'notes')
        }),
        ('ID Verification', {
            'fields': ('id_number', 'id_document', 'date_of_birth', 'address')
        }),
        ('Card/Invoice', {
            'fields': ('digital_card', 'physical_card', 'invoice')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
