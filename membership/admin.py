from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
# Use relative imports to get the models directly from models.py file
from .models import Member, Player, PlayerClubRegistration, Transfer, TransferAppeal, Membership
# Import from the invoice module within the models package
from .models.invoice import Invoice, InvoiceItem

class MemberAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'email', 'safa_id', 'role', 'status', 'has_qr_code')
    search_fields = ('first_name', 'last_name', 'email', 'safa_id')
    list_filter = ('role', 'status', 'gender')
    fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'date_of_birth')
        }),
        (_('Identification'), {
            'fields': ('safa_id', 'fifa_id', 'id_number', 'gender')
        }),
        (_('Membership Details'), {
            'fields': ('role', 'status', 'registration_date', 'expiry_date')
        }),
        (_('Club Affiliation'), {
            'fields': ('club',)
        }),
        (_('Address'), {
            'fields': ('street_address', 'suburb', 'city', 'state', 'postal_code', 'country'),
            'classes': ('collapse',),
        }),
        (_('Emergency Contact'), {
            'fields': ('emergency_contact', 'emergency_phone', 'medical_notes'),
            'classes': ('collapse',),
        }),
        (_('Media'), {
            'fields': ('profile_picture', 'qr_code_preview'),
        }),
    )
    readonly_fields = ('qr_code_preview',)
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = _('Name')
    
    def has_qr_code(self, obj):
        return bool(obj.safa_id)
    has_qr_code.boolean = True
    has_qr_code.short_description = _('QR Code')
    
    def qr_code_preview(self, obj):
        if obj.pk and obj.safa_id:
            qr_code = obj.generate_qr_code()
            if qr_code:
                return format_html(
                    '<img src="{}" style="max-width:150px; max-height:150px" />', qr_code
                )
        return _('QR code will be available after saving with a SAFA ID')
    qr_code_preview.short_description = _('QR Code Preview')
    
    def save_model(self, request, obj, form, change):
        # Ensure SAFA ID is generated
        if not obj.safa_id:
            obj.generate_safa_id()
        super().save_model(request, obj, form, change)
    
    actions = ['generate_safa_ids', 'generate_membership_cards', 'prepare_membership_cards']
    
    def generate_safa_ids(self, request, queryset):
        count = 0
        for member in queryset:
            if not member.safa_id:
                member.generate_safa_id()
                member.save(update_fields=['safa_id'])
                count += 1
        self.message_user(request, _('Generated SAFA IDs for {} members.').format(count))
    generate_safa_ids.short_description = _('Generate SAFA IDs for selected members')
    
    def generate_membership_cards(self, request, queryset):
        ready_count = 0
        not_ready_count = 0
        
        for member in queryset:
            if member.membership_card_ready:
                # Implement card generation logic here or queue it for processing
                ready_count += 1
            else:
                not_ready_count += 1
        
        if ready_count > 0:
            self.message_user(request, _('Queued {} membership cards for generation.').format(ready_count))
        if not_ready_count > 0:
            self.message_user(
                request, 
                _('Skipped {} members not ready for card generation (missing SAFA ID, inactive, or missing photo).').format(not_ready_count),
                level='WARNING'
            )
            
    generate_membership_cards.short_description = _('Generate membership cards')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('print-membership-cards/', 
                 self.admin_site.admin_view(self.print_membership_cards),
                 name='membership_print_cards'),
        ]
        return custom_urls + urls
    
    def print_membership_cards(self, request):
        """View for printing multiple membership cards"""
        # Get members with SAFA IDs and active status
        members = Member.objects.filter(
            safa_id__isnull=False,
            status='ACTIVE'
        )[:100]  # Limit to 100 to avoid performance issues
        
        context = {
            'title': "Print Membership Cards",
            'members': members,
        }
        return render(request, 'admin/membership/print_cards.html', context)
    
    def prepare_membership_cards(self, request, queryset):
        """Prepare membership cards for selected members"""
        members = queryset.filter(safa_id__isnull=False)
        missing_ids = queryset.filter(safa_id__isnull=True).count()
        
        if missing_ids:
            self.message_user(request, 
                            _("Warning: {} selected members don't have SAFA IDs and were skipped").format(missing_ids), 
                            level='WARNING')
        
        context = {
            'title': _("Print Membership Cards"),
            'members': members,
        }
        return render(request, 'admin/membership/print_cards.html', context)
    prepare_membership_cards.short_description = _("Prepare membership cards")

# Register other models with similar enhancements
@admin.register(Player)
class PlayerAdmin(MemberAdmin):
    list_display = ('get_full_name', 'email', 'safa_id', 'status', 'has_active_club')
    list_filter = ('status', 'gender')
    
    def has_active_club(self, obj):
        return PlayerClubRegistration.objects.filter(player=obj, status='ACTIVE').exists()
    has_active_club.boolean = True
    has_active_club.short_description = _('Active Club')

@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('player', 'from_club', 'to_club', 'status', 'request_date', 'display_transfer_fee')
    list_filter = ('status', 'request_date')
    search_fields = ('player__first_name', 'player__last_name', 'from_club__name', 'to_club__name')
    
    def display_transfer_fee(self, obj):
        if obj.transfer_fee is not None:
            return f"R {obj.transfer_fee:.2f} ZAR"
        return '-'
    display_transfer_fee.short_description = 'Transfer Fee (ZAR)'
    display_transfer_fee.admin_order_field = 'transfer_fee'

@admin.register(PlayerClubRegistration)
class PlayerClubRegistrationAdmin(admin.ModelAdmin):
    list_display = ('player', 'club', 'status', 'registration_date', 'position')
    list_filter = ('status', 'registration_date')
    search_fields = ('player__first_name', 'player__last_name', 'club__name')

admin.site.register(TransferAppeal)
admin.site.register(Membership)

# Invoice Administration
class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('description', 'quantity', 'unit_price', 'sub_total')
    readonly_fields = ('sub_total',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'player_name', 'club_name', 'amount', 
                   'issue_date', 'due_date', 'status', 'payment_method')
    list_filter = ('status', 'payment_method', 'issue_date', 'club')
    search_fields = ('invoice_number', 'reference', 'player__first_name', 
                    'player__last_name', 'club__name')
    readonly_fields = ('invoice_number', 'uuid')
    inlines = [InvoiceItemInline]
    date_hierarchy = 'issue_date'
    
    def player_name(self, obj):
        return obj.player.get_full_name()
    player_name.short_description = _("Player")
    
    def club_name(self, obj):
        return obj.club.name
    club_name.short_description = _("Club")
    
    actions = ['mark_as_paid', 'mark_as_overdue', 'export_selected_invoices']
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='PAID', payment_date=timezone.now().date())
        self.message_user(request, _("%s invoices have been marked as paid.") % updated)
    mark_as_paid.short_description = _("Mark selected invoices as paid")
    
    def mark_as_overdue(self, request, queryset):
        updated = queryset.update(status='OVERDUE')
        self.message_user(request, _("%s invoices have been marked as overdue.") % updated)
    mark_as_overdue.short_description = _("Mark selected invoices as overdue")
