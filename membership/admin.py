from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import models
# Import models directly from the models.py file 
from membership.models import Member, Player, PlayerClubRegistration, Transfer, TransferAppeal, Membership, Official
# Import Invoice models
from .invoice_models import Invoice, InvoiceItem, Vendor

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'role', 'status', 'club')
    search_fields = ('first_name', 'last_name', 'email', 'safa_id')
    list_filter = ('role', 'status', 'club')
    autocomplete_fields = ['club']

    # Remove duplicate list_display, search_fields, list_filter
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
    
    actions = ['generate_safa_ids', 'generate_membership_cards', 'prepare_membership_cards', 'send_payment_reminder']

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

    def send_payment_reminder(self, request, queryset):
        from django.core.mail import send_mail
        count = 0
        for member in queryset:
            if member.email:
                send_mail(
                    subject=_('Payment Reminder: Outstanding Invoices'),
                    message=_('You have outstanding invoices. Please log in to the system to view and settle your balance.'),
                    from_email='noreply@safaglobal.org',
                    recipient_list=[member.email],
                    fail_silently=True,
                )
                count += 1
        self.message_user(request, _(f"Sent payment reminders to {count} member(s)."))
    send_payment_reminder.short_description = _('Send payment reminder email to selected members')

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

@admin.register(Official)
class OfficialAdmin(MemberAdmin):
    list_display = ('get_full_name', 'email', 'safa_id', 'position', 'primary_association', 'status', 'is_approved')
    list_filter = ('status', 'is_approved', 'referee_level', 'primary_association')
    search_fields = ('first_name', 'last_name', 'email', 'safa_id', 'certification_number')
    fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'date_of_birth')
        }),
        (_('Identification'), {
            'fields': ('safa_id', 'fifa_id', 'id_number', 'gender')
        }),
        (_('Membership Details'), {
            'fields': ('role', 'status', 'registration_date', 'expiry_date', 'is_approved')
        }),
        (_('Position & Association'), {
            'fields': ('position', 'primary_association', 'associations', 'club')
        }),
        (_('Certification'), {
            'fields': ('certification_number', 'certification_document', 'certification_expiry_date', 'referee_level')
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
    
    actions = ['approve_officials', 'reject_officials']
    
    def approve_officials(self, request, queryset):
        updated = queryset.update(is_approved=True, status='ACTIVE')
        self.message_user(request, _(f"{updated} official(s) approved and activated."))
    approve_officials.short_description = _('Approve selected officials')
    
    def reject_officials(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, _(f"{updated} official(s) rejected."))
    reject_officials.short_description = _('Reject selected officials')

# Invoice Administration
class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('description', 'quantity', 'unit_price', 'sub_total')
    readonly_fields = ('sub_total',)

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'is_active', 'logo_thumbnail', 'created', 'modified')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('is_active',)
    readonly_fields = ('created', 'modified', 'logo_preview')
    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'phone', 'address', 'is_active')
        }),
        ('Logo', {
            'fields': ('logo', 'logo_preview')
        }),
    )

    def logo_thumbnail(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="30" height="30" style="border-radius: 50%;" />', obj.logo.url)
        return "No logo"
    logo_thumbnail.short_description = 'Logo'

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="200" height="200" style="max-width: 200px;" />', obj.logo.url)
        return "No logo uploaded."
    logo_preview.short_description = 'Logo Preview'
    logo_preview.allow_tags = True

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number', 'player', 'club', 'vendor', 'amount', 'status', 'issue_date', 'due_date', 'payment_date', 'is_paid', 'is_overdue'
    )
    search_fields = ('invoice_number', 'player__first_name', 'player__last_name', 'club__name', 'vendor__name')
    list_filter = ('status', 'invoice_type', 'issue_date', 'due_date', 'vendor')
    autocomplete_fields = ['player', 'club', 'issued_by', 'vendor']
    date_hierarchy = 'issue_date'
    readonly_fields = ('invoice_number', 'uuid', 'is_paid', 'is_overdue', 'get_payment_instructions')
    inlines = [InvoiceItemInline]
    actions = ['mark_selected_paid', 'mark_selected_overdue']

    def get_payment_instructions(self, obj):
        return obj.get_payment_instructions()
    get_payment_instructions.short_description = 'Payment Instructions'

    def mark_selected_paid(self, request, queryset):
        """Bulk action: Mark selected invoices as paid."""
        paid_count = 0
        for invoice in queryset:
            if invoice.status != 'PAID':
                invoice.mark_as_paid()
                paid_count += 1
        self.message_user(request, f"{paid_count} invoice(s) marked as paid.")
    mark_selected_paid.short_description = "Mark selected invoices as paid"

    def mark_selected_overdue(self, request, queryset):
        """Bulk action: Mark selected invoices as overdue."""
        overdue_count = queryset.exclude(status='OVERDUE').update(status='OVERDUE')
        self.message_user(request, f"{overdue_count} invoice(s) marked as overdue.")
    mark_selected_overdue.short_description = "Mark selected invoices as overdue"

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'description', 'quantity', 'unit_price', 'sub_total')
    search_fields = ('invoice__invoice_number', 'description')
    autocomplete_fields = ['invoice']
    readonly_fields = ('sub_total',)
    
    def sub_total(self, obj):
        return f"R{obj.sub_total:.2f}"
    sub_total.short_description = "Sub Total"
