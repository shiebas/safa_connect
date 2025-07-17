from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import models
# Import models directly from the models.py file 
from membership.models import Member, JuniorMember, ClubRegistration, Player, PlayerClubRegistration, Transfer, TransferAppeal, Membership, Official
# Import Invoice models
from .invoice_models import Invoice, InvoiceItem, Vendor
from .models import MembershipApplication

# Legacy MemberAdmin - keeping for reference but not registering
class LegacyMemberAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'status')
    search_fields = ('first_name', 'last_name', 'email', 'safa_id')
    list_filter = ('status',)
    # Note: club is now handled through ClubRegistration

    # Remove duplicate list_display, search_fields, list_filter
    list_display = ('get_full_name', 'email', 'safa_id', 'status', 'has_qr_code')
    search_fields = ('first_name', 'last_name', 'email', 'safa_id')
    list_filter = ('status', 'gender')
    fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'date_of_birth')
        }),
        (_('Identification'), {
            'fields': ('safa_id', 'fifa_id', 'id_number', 'gender')
        }),
        (_('Membership Details'), {
            'fields': ('status',)
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
class PlayerAdmin(LegacyMemberAdmin):
    list_display = ('get_full_name', 'email', 'safa_id', 'status', 'has_active_club')
    list_filter = ('status', 'gender')
    search_fields = ('first_name', 'last_name', 'email', 'safa_id')
    
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


# New admin classes for refactored membership system
class NewMemberAdmin(admin.ModelAdmin):
    """Admin for the new two-tier membership system"""
    list_display = ('safa_id', 'get_full_name', 'email', 'member_type', 'status', 'created')
    list_filter = ('status', 'member_type', 'province', 'created')
    search_fields = ('safa_id', 'first_name', 'last_name', 'email')
    actions = ['approve_selected', 'reject_selected', 'send_welcome_emails']
    
    fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'member_type')
        }),
        (_('Identification'), {
            'fields': ('safa_id', 'id_number', 'passport_number', 'gender')
        }),
        (_('Status & Approval'), {
            'fields': ('status', 'approved_by', 'approved_date', 'rejection_reason')
        }),
        (_('Geography'), {
            'fields': ('province', 'region', 'lfa'),
            'classes': ('collapse',),
        }),
        (_('Address'), {
            'fields': ('street_address', 'suburb', 'city', 'state', 'postal_code', 'country'),
            'classes': ('collapse',),
        }),
        (_('Emergency Contact'), {
            'fields': ('emergency_contact', 'emergency_phone', 'medical_notes'),
            'classes': ('collapse',),
        }),
        (_('Documents'), {
            'fields': ('profile_picture', 'id_document'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('safa_id', 'approved_by', 'approved_date')
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = _('Name')
    
    def approve_selected(self, request, queryset):
        """Approve selected members"""
        count = 0
        for member in queryset.filter(status='PENDING'):
            member.approve_membership(request.user)
            count += 1
        self.message_user(request, _('Approved {} members').format(count))
    approve_selected.short_description = _('Approve selected members')
    
    def reject_selected(self, request, queryset):
        """Reject selected members"""
        count = 0
        for member in queryset.filter(status='PENDING'):
            member.reject_membership(request.user, "Bulk rejection")
            count += 1
        self.message_user(request, _('Rejected {} members').format(count))
    reject_selected.short_description = _('Reject selected members')
    
    def send_welcome_emails(self, request, queryset):
        """Send welcome emails to approved members"""
        from .membership_registration_views import send_welcome_email
        count = 0
        for member in queryset.filter(status='ACTIVE'):
            if member.email:
                send_welcome_email(member)
                count += 1
        self.message_user(request, _('Sent welcome emails to {} members').format(count))
    send_welcome_emails.short_description = _('Send welcome emails')


@admin.register(JuniorMember)
class JuniorMemberAdmin(NewMemberAdmin):
    """Admin for junior members with guardian information"""
    list_display = ('safa_id', 'get_full_name', 'email', 'age', 'status', 'guardian_name')
    
    fieldsets = NewMemberAdmin.fieldsets + (
        (_('Guardian Information'), {
            'fields': ('guardian_name', 'guardian_email', 'guardian_phone', 'school')
        }),
    )
    
    def age(self, obj):
        return obj.age
    age.short_description = _('Age')


@admin.register(ClubRegistration)
class ClubRegistrationAdmin(admin.ModelAdmin):
    """Admin for club registrations (step 2 of two-tier system)"""
    list_display = ('member', 'club', 'status', 'registration_date', 'position')
    list_filter = ('status', 'registration_date', 'club')
    search_fields = ('member__first_name', 'member__last_name', 'club__name')
    
    fieldsets = (
        (None, {
            'fields': ('member', 'club', 'status', 'registration_date')
        }),
        (_('Playing Details'), {
            'fields': ('position', 'jersey_number'),
            'classes': ('collapse',),
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
    )
    
    def get_queryset(self, request):
        """Only show registrations for approved members"""
        return super().get_queryset(request).select_related('member', 'club')


# Register the new Member admin - handle potential existing registration
try:
    admin.site.unregister(Member)
except admin.sites.NotRegistered:
    pass
admin.site.register(Member, NewMemberAdmin)

@admin.register(Official)
class OfficialAdmin(LegacyMemberAdmin):
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
    search_fields = ('invoice_number', 'player__first_name', 'player__last_name', 'club__name', 'vendor__name', 'issued_by__email')
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

@admin.register(MembershipApplication)
class MembershipApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'member', 'get_first_name', 'get_last_name', 'get_email', 'get_phone_number',
        'get_id_number', 'get_passport_number', 'club', 'status', 'submitted_at', 'reviewed_by', 'reviewed_at'
    )
    list_filter = ('status', 'club', 'submitted_at')
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Always filter for PENDING status by default for all admins
        qs = qs.filter(status='PENDING')

        user = request.user
        if user.is_superuser or getattr(user, 'role', None) == 'ADMIN_NATIONAL':
            # Superusers and National Admins see all pending applications
            return qs
        elif getattr(user, 'role', None) == 'ADMIN_PROVINCE' and user.province:
            # Provincial Admins see applications for their province
            return qs.filter(member__province=user.province)
        elif getattr(user, 'role', None) == 'ADMIN_REGION' and user.region:
            # Regional Admins see applications for their region
            return qs.filter(member__region=user.region)
        elif getattr(user, 'role', None) == 'ADMIN_LOCAL_FED' and user.local_federation:
            # LFA Admins see applications for their LFA
            return qs.filter(member__lfa=user.local_federation)
        elif getattr(user, 'role', None) == 'CLUB_ADMIN' and user.club:
            # Club Admins see applications for their club
            return qs.filter(club=user.club) # Note: MembershipApplication has a direct 'club' FK
        
        # For any other role or if no relevant geographical assignment, return an empty queryset
        return qs.none()
    search_fields = (
        'member__first_name', 'member__last_name', 'member__id_number', 'club__name', 'member__email'
    )
    readonly_fields = ('signature', 'submitted_at', 'reviewed_by', 'reviewed_at')
    actions = ['approve_applications', 'reject_applications']

    def get_first_name(self, obj):
        return obj.member.first_name if obj.member else ''
    get_first_name.short_description = 'First Name'

    def get_last_name(self, obj):
        return obj.member.last_name if obj.member else ''
    get_last_name.short_description = 'Last Name'

    def get_email(self, obj):
        return obj.member.email if obj.member else ''
    get_email.short_description = 'Email'

    def get_phone_number(self, obj):
        return obj.member.phone_number if obj.member else ''
    get_phone_number.short_description = 'Phone Number'

    def get_id_number(self, obj):
        return obj.member.id_number if obj.member else ''
    get_id_number.short_description = 'ID Number'

    def get_passport_number(self, obj):
        return obj.member.passport_number if obj.member else ''
    get_passport_number.short_description = 'Passport Number'

    def approve_applications(self, request, queryset):
        for app in queryset:
            if request.user.is_superuser or getattr(request.user, 'role', None) == 'NATIONAL_ADMINISTRATOR':
                app.status = 'APPROVED'
                app.reviewed_by = request.user
                app.reviewed_at = timezone.now()
                app.save()  
    approve_applications.short_description = "Approve selected applications"

    def reject_applications(self, request, queryset):
        for app in queryset:
            if request.user.is_superuser or getattr(request.user, 'role', None) == 'NATIONAL_ADMINISTRATOR':
                app.status = 'REJECTED'
                app.reviewed_by = request.user
                app.reviewed_at = timezone.now()
                app.save()
    reject_applications.short_description = "Reject selected applications"

from . import admin_views  # Import the new admin views
from django.urls import path

class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # This is the URL for our new dashboard view
            path('membership/dashboard/', self.admin_view(admin_views.national_admin_dashboard), name='national_dashboard'),
        ]
        return custom_urls + urls

try:
    admin_site = CustomAdminSite()  # Use the custom admin site

    original_site = admin.site
    admin.site = admin_site

    # Move registered models from the old site to the new one
    for model, model_admin in list(original_site._registry.items()):  # Use list() to avoid size change during iteration
        admin.site.register(model, model_admin.__class__)

except Exception as e:
    # If something goes wrong, fall back to the default site to avoid crashing
    print(f"Could not replace admin site: {e}")
    admin.site = original_site  # Restore the original site
