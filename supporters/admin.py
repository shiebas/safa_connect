from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import SupporterProfile, SupporterPreferences


@admin.register(SupporterPreferences)
class SupporterPreferencesAdmin(admin.ModelAdmin):
    list_display = ['supporter_name', 'total_selected', 'communication_frequency', 'email_notifications', 'updated_at']
    list_filter = [
        'communication_frequency', 'email_notifications', 'sms_alerts', 
        'discount_tickets', 'vip_experiences', 'official_jerseys', 
        'match_travel_packages', 'exclusive_content', 'community_events'
    ]
    search_fields = ['supporterprofile__user__first_name', 'supporterprofile__user__last_name', 'supporterprofile__user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Communication Preferences', {
            'fields': (
                'communication_frequency',
                ('email_notifications', 'sms_alerts', 'push_notifications', 'whatsapp_updates')
            ),
            'description': 'How and how often the supporter wants to receive communications'
        }),
        ('Tickets & Events', {
            'fields': (
                ('discount_tickets', 'vip_experiences'),
                ('international_matches', 'local_matches', 'youth_matches')
            ),
            'classes': ('collapse',)
        }),
        ('Merchandise & Retail', {
            'fields': (
                ('official_jerseys', 'casual_clothing'),
                ('limited_editions', 'seasonal_sales')
            ),
            'classes': ('collapse',)
        }),
        ('Travel & Hospitality', {
            'fields': (
                ('match_travel_packages', 'accommodation_deals'),
                ('transport_offers', 'international_tours')
            ),
            'classes': ('collapse',)
        }),
        ('Digital & Media', {
            'fields': (
                ('exclusive_content', 'player_interviews'),
                ('live_streaming', 'podcasts_videos')
            ),
            'classes': ('collapse',)
        }),
        ('Community & Events', {
            'fields': (
                ('community_events', 'coaching_clinics'),
                ('player_meetups', 'charity_initiatives')
            ),
            'classes': ('collapse',)
        }),
        ('Food & Beverage', {
            'fields': (
                ('stadium_dining', 'partner_restaurant_deals', 'catering_packages'),
            ),
            'classes': ('collapse',)
        }),
        ('Financial Services', {
            'fields': (
                ('insurance_products', 'banking_offers', 'investment_opportunities'),
            ),
            'classes': ('collapse',)
        }),
        ('Special Interests', {
            'fields': (
                ('youth_development', 'womens_football'),
                ('disability_football', 'referee_programs', 'coaching_development')
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ]
    
    def supporter_name(self, obj):
        try:
            return obj.supporterprofile.user.get_full_name()
        except:
            return "No Supporter Profile"
    supporter_name.short_description = 'Supporter'
    
    def total_selected(self, obj):
        count = obj.total_preferences_selected
        color = 'green' if count > 10 else 'orange' if count > 5 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} preferences</span>',
            color, count
        )
    total_selected.short_description = 'Preferences Selected'


@admin.register(SupporterProfile)
class SupporterProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'favorite_club', 'membership_type', 'is_verified', 'created_at',
        'location_city', 'location_province', 'has_location', 'has_invoice', 
        'event_tickets_count', 'preferences_summary'
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
    
    def event_tickets_count(self, obj):
        try:
            # Import here to avoid circular imports
            from events.models import Ticket
            count = Ticket.objects.filter(supporter=obj).count()
            if count > 0:
                return format_html(
                    '<a href="{}?supporter__id__exact={}">{} tickets</a>',
                    reverse('admin:events_ticket_changelist'),
                    obj.id,
                    count
                )
            return '0'
        except:
            return '0'
    event_tickets_count.short_description = 'Event Tickets'
    
    def preferences_summary(self, obj):
        if obj.preferences:
            count = obj.preferences.total_preferences_selected
            color = 'green' if count > 10 else 'orange' if count > 5 else 'red'
            return format_html(
                '<a href="{}" style="color: {}; font-weight: bold;">{} preferences</a>',
                reverse('admin:supporters_supporterpreferences_change', args=[obj.preferences.id]),
                color, count
            )
        return format_html('<span style="color: red;">No preferences</span>')
    preferences_summary.short_description = 'Preferences'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'favorite_club', 'membership_type', 'preferences', 'is_verified', 'notes')
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
