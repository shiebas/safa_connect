from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponse
from .models import DigitalCard, PhysicalCard, PhysicalCardTemplate

@admin.register(DigitalCard)
class DigitalCardAdmin(admin.ModelAdmin):
    list_display = [
        'card_number', 'user', 'status', 'issued_date', 
        'expires_date', 'is_valid'
    ]
    list_filter = ['status', 'issued_date', 'expires_date']
    search_fields = ['card_number', 'user__email', 'user__name', 'user__surname']
    readonly_fields = [
        'card_number', 'card_uuid', 'issued_date', 'last_updated',
        'qr_code_data', 'card_type'
    ]
    
    fieldsets = (
        ('Card Information', {
            'fields': ('user', 'template', 'card_number', 'card_uuid', 'card_type')
        }),
        ('Status', {
            'fields': ('status', 'expires_date')
        }),
        ('QR Code', {
            'fields': ('qr_code_data', 'qr_code_version'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('issued_date', 'last_updated'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['suspend_cards', 'reactivate_cards', 'regenerate_qr_codes']
    
    def suspend_cards(self, request, queryset):
        updated = queryset.update(status='SUSPENDED')
        self.message_user(
            request,
            f'{updated} digital card(s) suspended.',
            messages.WARNING
        )
    suspend_cards.short_description = "Suspend selected digital cards"
    
    def reactivate_cards(self, request, queryset):
        updated = queryset.update(status='ACTIVE')
        self.message_user(
            request,
            f'{updated} digital card(s) reactivated.',
            messages.SUCCESS
        )
    reactivate_cards.short_description = "Reactivate selected digital cards"
    
    def regenerate_qr_codes(self, request, queryset):
        updated = 0
        for card in queryset:
            card.qr_code_version += 1
            card.save()  # This will regenerate QR data
            updated += 1
        
        self.message_user(
            request,
            f'{updated} QR code(s) regenerated.',
            messages.SUCCESS
        )
    regenerate_qr_codes.short_description = "Regenerate QR codes"

@admin.register(PhysicalCardTemplate)
class PhysicalCardTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_active', 'created_date']
    list_filter = ['template_type', 'is_active', 'created_date']
    search_fields = ['name']
    
    fieldsets = (
        ('Template Info', {
            'fields': ('name', 'template_type', 'is_active')
        }),
        ('Design Images', {
            'fields': ('card_front_image', 'card_back_image')
        }),
        ('Field Positions', {
            'fields': (
                ('name_position_x', 'name_position_y'),
                ('photo_position_x', 'photo_position_y'),
                ('qr_position_x', 'qr_position_y')
            ),
            'description': 'Pixel coordinates for dynamic content placement'
        }),
        ('Card Specifications', {
            'fields': ('card_width', 'card_height'),
            'description': 'Card dimensions in pixels at 300 DPI'
        }),
    )

@admin.register(PhysicalCard)
class PhysicalCardAdmin(admin.ModelAdmin):
    list_display = [
        'card_number', 'user', 'template', 'print_status', 'ordered_date',
        'shipped_date', 'tracking_number'
    ]
    list_filter = ['print_status', 'template', 'ordered_date', 'shipped_date']
    search_fields = ['card_number', 'user__email', 'user__name', 'user__surname', 'tracking_number']
    readonly_fields = ['ordered_date', 'card_type']
    
    fieldsets = (
        ('Card Information', {
            'fields': ('user', 'card_number', 'template', 'card_type')
        }),
        ('Print Status', {
            'fields': ('print_status', 'printed_date')
        }),
        ('Shipping', {
            'fields': ('shipping_address', 'tracking_number', 'shipped_date', 'delivered_date')
        }),
        ('Timestamps', {
            'fields': ('ordered_date',)
        }),
    )
    
    actions = ['mark_printed', 'mark_shipped', 'mark_delivered', 'generate_print_ready_cards']
    
    def generate_print_ready_cards(self, request, queryset):
        """Generate print-ready PDF for selected cards"""
        try:
            from .card_generator import generate_print_ready_pdf
        except ImportError:
            self.message_user(
                request, 
                'PDF generation requires additional packages. Install with: pip install reportlab', 
                messages.ERROR
            )
            return
        
        pending_cards = queryset.filter(print_status='PENDING')
        if not pending_cards:
            self.message_user(request, 'No pending cards selected.', messages.WARNING)
            return
            
        try:
            pdf_file = generate_print_ready_pdf(pending_cards)
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="safa_cards_batch_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf"'
            return response
        except Exception as e:
            self.message_user(request, f'Error generating PDF: {str(e)}', messages.ERROR)
    
    generate_print_ready_cards.short_description = "Generate print-ready PDF"
