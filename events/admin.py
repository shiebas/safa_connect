from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum, Count
from .models import Stadium, SeatMap, InternationalMatch, Ticket, TicketGroup


@admin.register(Stadium)
class StadiumAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'province', 'capacity', 'seat_count', 'is_active']
    list_filter = ['province', 'surface_type', 'is_active', 'has_roof']
    search_fields = ['name', 'short_name', 'city']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ('name', 'short_name', 'capacity')
        }),
        ('Location', {
            'fields': ('city', 'province', 'address')
        }),
        ('Stadium Details', {
            'fields': ('surface_type', 'has_roof', 'has_lighting', 'parking_spaces')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'contact_phone', 'contact_email')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    ]
    
    def seat_count(self, obj):
        count = obj.seats.count()
        if count > 0:
            return format_html(
                '<a href="{}?stadium__id__exact={}">{} seats</a>',
                reverse('admin:events_seatmap_changelist'),
                obj.id,
                count
            )
        return '0 seats'
    seat_count.short_description = 'Configured Seats'


@admin.register(SeatMap)
class SeatMapAdmin(admin.ModelAdmin):
    list_display = ['stadium', 'section', 'row', 'seat_number', 'price_tier', 'base_price', 'accessibility_info', 'is_active']
    list_filter = ['stadium', 'price_tier', 'is_wheelchair_accessible', 'has_restricted_view', 'is_active']
    search_fields = ['stadium__name', 'section', 'row', 'seat_number']
    list_editable = ['base_price', 'is_active']
    
    fieldsets = [
        ('Seat Location', {
            'fields': ('stadium', 'section', 'row', 'seat_number')
        }),
        ('Pricing', {
            'fields': ('price_tier', 'base_price')
        }),
        ('Accessibility', {
            'fields': ('is_wheelchair_accessible', 'has_restricted_view')
        }),
        ('Status', {
            'fields': ('is_active', 'notes')
        }),
    ]
    
    def accessibility_info(self, obj):
        icons = []
        if obj.is_wheelchair_accessible:
            icons.append('♿ Wheelchair')
        if obj.has_restricted_view:
            icons.append('⚠️ Restricted View')
        return ' | '.join(icons) if icons else '-'
    accessibility_info.short_description = 'Accessibility'


@admin.register(InternationalMatch)
class InternationalMatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'match_date', 'stadium', 'sales_status_display', 'tickets_sold_display', 'total_revenue', 'is_featured']
    list_filter = ['match_type', 'stadium', 'is_active', 'is_featured', 'match_date']
    search_fields = ['name', 'home_team', 'away_team', 'safa_id']
    readonly_fields = ['safa_id', 'tickets_sold', 'created_at', 'updated_at']
    list_editable = ['is_featured']
    date_hierarchy = 'match_date'
    
    fieldsets = [
        ('Match Details', {
            'fields': ('name', 'description', 'match_type', 'safa_id')
        }),
        ('Teams', {
            'fields': ('home_team', 'away_team')
        }),
        ('Venue & Schedule', {
            'fields': ('stadium', 'match_date')
        }),
        ('Ticket Sales', {
            'fields': ('tickets_available', 'tickets_sold', 'sales_open_date', 'sales_close_date')
        }),
        ('Pricing & Discounts', {
            'fields': ('enable_early_bird', 'early_bird_discount', 'early_bird_end_date')
        }),
        ('Group Bookings', {
            'fields': ('enable_group_discount', 'group_size_minimum', 'group_discount_percentage')
        }),
        ('Status & Features', {
            'fields': ('is_active', 'is_featured')
        }),
    ]
    
    def sales_status_display(self, obj):
        status = obj.sales_status
        colors = {
            'PENDING': '#6c757d',
            'OPEN': '#28a745',
            'SOLD_OUT': '#dc3545',
            'CLOSED': '#6c757d'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(status, '#000'),
            status.replace('_', ' ')
        )
    sales_status_display.short_description = 'Sales Status'
    
    def tickets_sold_display(self, obj):
        percentage = (obj.tickets_sold / obj.tickets_available * 100) if obj.tickets_available > 0 else 0
        color = '#dc3545' if percentage > 90 else '#ffc107' if percentage > 70 else '#28a745'
        return format_html(
            '<span style="color: {};">{}/{} ({}%)</span>',
            color,
            obj.tickets_sold,
            obj.tickets_available,
            round(percentage, 1)
        )
    tickets_sold_display.short_description = 'Tickets Sold'
    
    def total_revenue(self, obj):
        revenue = obj.tickets.filter(status__in=['PAID', 'USED']).aggregate(
            total=Sum('final_price')
        )['total'] or 0
        return f"R {revenue:,.2f}"
    total_revenue.short_description = 'Revenue'


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'match', 'supporter_name', 'seat_info', 'final_price', 'status', 'purchased_at']
    list_filter = ['status', 'match', 'seat__price_tier', 'purchased_at']
    search_fields = ['ticket_number', 'qr_code', 'supporter__user__first_name', 'supporter__user__last_name']
    readonly_fields = ['ticket_number', 'qr_code', 'barcode', 'purchased_at', 'used_at']
    date_hierarchy = 'purchased_at'
    
    fieldsets = [
        ('Ticket Information', {
            'fields': ('ticket_number', 'match', 'seat', 'status')
        }),
        ('Buyer Information', {
            'fields': ('supporter',)
        }),
        ('Pricing', {
            'fields': ('base_price', 'discount_applied', 'final_price')
        }),
        ('Payment', {
            'fields': ('invoice',)
        }),
        ('Digital Ticket', {
            'fields': ('qr_code', 'barcode')
        }),
        ('Timestamps', {
            'fields': ('purchased_at', 'used_at')
        }),
        ('Additional Information', {
            'fields': ('special_requirements', 'notes')
        }),
    ]
    
    def supporter_name(self, obj):
        return obj.supporter.user.get_full_name()
    supporter_name.short_description = 'Supporter'
    
    def seat_info(self, obj):
        return f"{obj.seat.section}{obj.seat.row}-{obj.seat.seat_number} ({obj.seat.price_tier})"
    seat_info.short_description = 'Seat'


@admin.register(TicketGroup)
class TicketGroupAdmin(admin.ModelAdmin):
    list_display = ['group_number', 'group_name', 'match', 'primary_contact_name', 'group_size', 'total_amount', 'status']
    list_filter = ['status', 'match', 'created_at']
    search_fields = ['group_number', 'group_name', 'primary_contact__user__first_name', 'primary_contact__user__last_name']
    readonly_fields = ['group_number', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Group Information', {
            'fields': ('group_number', 'group_name', 'match', 'primary_contact')
        }),
        ('Group Details', {
            'fields': ('group_size', 'total_amount', 'discount_applied')
        }),
        ('Payment', {
            'fields': ('invoice', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    ]
    
    def primary_contact_name(self, obj):
        return obj.primary_contact.user.get_full_name()
    primary_contact_name.short_description = 'Primary Contact'


# Admin site customization
admin.site.site_header = "SAFA Global Administration"
admin.site.site_title = "SAFA Admin"
admin.site.index_title = "Welcome to SAFA Global Administration"
