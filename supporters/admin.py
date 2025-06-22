from django.contrib import admin
from .models import SupporterProfile

@admin.register(SupporterProfile)
class SupporterProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'favorite_club', 'membership_type', 'is_verified', 'created_at',
        'location_city', 'location_province', 'has_location', 'has_invoice'
    )
    list_filter = ('membership_type', 'is_verified', 'favorite_club', 'location_province', 'location_country')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'id_number', 'location_city')
    readonly_fields = ('created_at', 'location_timestamp')
    
    def has_location(self, obj):
        return bool(obj.latitude and obj.longitude)
    has_location.boolean = True
    has_location.short_description = 'Has Location'
    
    def has_invoice(self, obj):
        return bool(obj.invoice)
    has_invoice.boolean = True
    has_invoice.short_description = 'Has Invoice'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'favorite_club', 'membership_type', 'is_verified', 'notes')
        }),
        ('ID Verification', {
            'fields': ('id_number', 'id_document', 'date_of_birth', 'address')
        }),
        ('Location Information', {
            'fields': (
                ('latitude', 'longitude'), 
                ('location_city', 'location_province', 'location_country'),
                'location_accuracy', 'location_timestamp'
            ),
            'description': 'Geolocation data captured during registration'
        }),
        ('Card/Invoice', {
            'fields': ('digital_card', 'physical_card', 'invoice')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
