# membership/admin.py - FINAL ENHANCED VERSION
# This replaces your existing admin with SAFA invoice integration

from django.contrib import admin
from django.urls import path, include, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render, redirect
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import models
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from decimal import Decimal

# Import existing models
from membership.models import Member, JuniorMember, ClubRegistration, Transfer, TransferAppeal, Membership
from registration.models import Player, PlayerClubRegistration, Official
from .models import Invoice, InvoiceItem, Vendor, MembershipApplication

# Import new SAFA models and manager
try:
    from .config_models import (
        SAFASeasonConfig, SAFAFeeStructure, SAFAPaymentPlan, 
        SAFAInvoiceSequence, SAFAInvoiceTemplate
    )
    from .enhanced_models import InvoicePayment, InvoiceInstallment, InvoiceNote, InvoiceDocument
    from .safa_invoice_manager import SAFAInvoiceManager
    SAFA_SYSTEM_AVAILABLE = True
except ImportError:
    SAFA_SYSTEM_AVAILABLE = False
    # print("⚠️ SAFA system not yet migrated - some features will be unavailable")


class SAFAAccountsAdminMixin:
    """Mixin to restrict admin access to NATIONAL_ADMIN_ACCOUNTS only"""
    
    def has_module_permission(self, request):
        return (
            request.user.is_superuser or 
            getattr(request.user, 'role', None) in ['ADMIN_NATIONAL', 'ADMIN_NATIONAL_ACCOUNTS']
        )
    
    def has_view_permission(self, request, obj=None):
        return (
            request.user.is_superuser or 
            getattr(request.user, 'role', None) in ['ADMIN_NATIONAL', 'ADMIN_NATIONAL_ACCOUNTS']
        )
    
    def has_add_permission(self, request):
        return (
            request.user.is_superuser or 
            getattr(request.user, 'role', None) in ['ADMIN_NATIONAL', 'ADMIN_NATIONAL_ACCOUNTS']
        )
    
    def has_change_permission(self, request, obj=None):
        return (
            request.user.is_superuser or 
            getattr(request.user, 'role', None) in ['ADMIN_NATIONAL', 'ADMIN_NATIONAL_ACCOUNTS']
        )
    
    def has_delete_permission(self, request, obj=None):
        return (
            request.user.is_superuser or 
            getattr(request.user, 'role', None) == 'ADMIN_NATIONAL'  # Only National Admin can delete
        )


# ============================================================================
# SAFA CONFIGURATION ADMINS (NEW - Only if SAFA system is available)
# ============================================================================

if SAFA_SYSTEM_AVAILABLE:
    @admin.register(SAFASeasonConfig)
    class SAFASeasonConfigAdmin(SAFAAccountsAdminMixin, admin.ModelAdmin):
        list_display = [
            'season_year', 'season_period', 'vat_rate_display', 'payment_due_days', 
            'is_active', 'is_renewal_season', 'created_by', 'invoice_count'
        ]
        list_filter = ['is_active', 'is_renewal_season', 'created_by']
        search_fields = ['season_year']
        readonly_fields = ['created_by', 'created_at', 'updated_at']
        
        fieldsets = (
            ('Season Information', {
                'fields': ('season_year', 'season_start_date', 'season_end_date')
            }),
            ('Financial Configuration', {
                'fields': ('vat_rate', 'payment_due_days')
            }),
            ('Season Status', {
                'fields': ('is_active', 'is_renewal_season')
            }),
            ('Administrative', {
                'fields': ('created_by', 'created_at', 'updated_at'),
                'classes': ('collapse',)
            })
        )
        
        actions = ['activate_season', 'generate_renewal_invoices', 'duplicate_season_config']
        
        def season_period(self, obj):
            return f"{obj.season_start_date} to {obj.season_end_date}"
        season_period.short_description = "Season Period"
        
        def vat_rate_display(self, obj):
            return f"{(obj.vat_rate * 100):.1f}%"
        vat_rate_display.short_description = "VAT Rate"
        
        def invoice_count(self, obj):
            count = obj.invoices.count() if hasattr(obj, 'invoices') else 0
            if count > 0:
                url = reverse('admin:membership_invoice_changelist') + f'?season_config__id__exact={obj.id}'
                return format_html('<a href="{}">{} invoices</a>', url, count)
            return "0 invoices"
        invoice_count.short_description = "Invoices"
        
        def save_model(self, request, obj, form, change):
            if not change:  # New object
                obj.created_by = request.user
            super().save_model(request, obj, form, change)
        
        def activate_season(self, request, queryset):
            if queryset.count() != 1:
                messages.error(request, "Please select exactly one season to activate.")
                return
            
            season = queryset.first()
            # Deactivate all other seasons
            SAFASeasonConfig.objects.update(is_active=False)
            # Activate selected season
            season.is_active = True
            season.save()
            
            messages.success(request, f"Season {season.season_year} has been activated.")
        activate_season.short_description = "Activate selected season"
        
        def generate_renewal_invoices(self, request, queryset):
            if queryset.count() != 1:
                messages.error(request, "Please select exactly one season for renewal generation.")
                return
            
            season = queryset.first()
            try:
                count, _ = SAFAInvoiceManager.generate_season_renewal_invoices(season)
                messages.success(request, f"Generated {count} renewal invoices for season {season.season_year}.")
            except Exception as e:
                messages.error(request, f"Error generating renewals: {str(e)}")
        generate_renewal_invoices.short_description = "Generate renewal invoices for season"


    @admin.register(SAFAFeeStructure)
    class SAFAFeeStructureAdmin(SAFAAccountsAdminMixin, admin.ModelAdmin):
        list_display = [
            'entity_type', 'season_year', 'annual_fee_display', 'minimum_fee_display',
            'is_pro_rata', 'created_by'
        ]
        list_filter = ['season_config__season_year', 'entity_type', 'is_pro_rata']
        search_fields = ['entity_type', 'description']
        readonly_fields = ['created_by', 'created_at', 'updated_at']
        
        def season_year(self, obj):
            return obj.season_config.season_year
        season_year.short_description = "Season"
        
        def annual_fee_display(self, obj):
            return f"R{obj.annual_fee:,.2f}"
        annual_fee_display.short_description = "Annual Fee"
        
        def minimum_fee_display(self, obj):
            if obj.minimum_fee:
                return f"R{obj.minimum_fee:,.2f}"
            return "-"
        minimum_fee_display.short_description = "Minimum Fee"
        
        def save_model(self, request, obj, form, change):
            if not change:
                obj.created_by = request.user
            super().save_model(request, obj, form, change)


    @admin.register(SAFAPaymentPlan)
    class SAFAPaymentPlanAdmin(SAFAAccountsAdminMixin, admin.ModelAdmin):
        list_display = [
            'name', 'season_year', 'frequency', 'number_of_installments', 
            'installment_fee_display', 'minimum_amount_display', 'is_active'
        ]
        list_filter = ['season_config__season_year', 'frequency', 'is_active']
        search_fields = ['name']
        
        def season_year(self, obj):
            return obj.season_config.season_year
        season_year.short_description = "Season"
        
        def installment_fee_display(self, obj):
            return f"R{obj.installment_fee:,.2f}"
        installment_fee_display.short_description = "Processing Fee"
        
        def minimum_amount_display(self, obj):
            return f"R{obj.minimum_amount:,.2f}"
        minimum_amount_display.short_description = "Minimum Amount"


# ============================================================================
# ENHANCED EXISTING ADMINS
# ============================================================================

class NewMemberAdmin(admin.ModelAdmin):
    """Enhanced version of your existing Member admin with SAFA integration"""
    
    class Media:
        js = ("admin/js/jquery.init.js", "admin/js/member_admin_dynamic_fields.js",)
    
    list_display = ('safa_id_link', 'get_full_name', 'email', 'member_type', 'status', 'created', 'club', 'association', 'invoice_status')
    list_display_links = ('get_full_name',)
    list_filter = ('status', 'member_type', 'province', 'created', 'club', 'association')
    search_fields = ('safa_id', 'first_name', 'last_name', 'email', 'id_number', 'club__name', 'association__name')
    actions = ['approve_selected', 'reject_selected', 'send_welcome_emails', 'generate_safa_invoices', 'send_payment_reminders']
    
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
            'fields': ('province', 'region', 'lfa', 'association', 'club'),
            'classes': ('collapse',),
        }),
    )
    
    if SAFA_SYSTEM_AVAILABLE:
        fieldsets += (
            (_('SAFA Invoice Information'), {
                'fields': ('invoice_summary', 'outstanding_amount_display'),
                'classes': ('collapse',),
            }),
        )
    
    fieldsets += (
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
    
    readonly_fields = ['safa_id', 'approved_by', 'approved_date']
    if SAFA_SYSTEM_AVAILABLE:
        readonly_fields += ['invoice_summary', 'outstanding_amount_display']

    def safa_id_link(self, obj):
        url = reverse("admin:membership_member_change", args=[obj.id])
        return format_html(f'<a href="{url}">{obj.safa_id}</a>')
    safa_id_link.short_description = "SAFA ID"
    safa_id_link.admin_order_field = "safa_id"

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = _('Name')
    
    def invoice_status(self, obj):
        """Show invoice payment status"""
        if not SAFA_SYSTEM_AVAILABLE:
            return "N/A"
        
        try:
            # Get invoices for this member
            player_invoices = obj.player_invoices.filter(status__in=['PENDING', 'OVERDUE']) if hasattr(obj, 'player_invoices') else []
            official_invoices = obj.official_invoices.filter(status__in=['PENDING', 'OVERDUE']) if hasattr(obj, 'official_invoices') else []
            
            total_unpaid = len(player_invoices) + len(official_invoices)
            
            if total_unpaid == 0:
                return format_html('<span style="color: green;">✓ Paid</span>')
            else:
                return format_html(f'<span style="color: red;">⚠ {total_unpaid} unpaid</span>')
        except:
            return "Unknown"
    invoice_status.short_description = "Invoice Status"
    
    def invoice_summary(self, obj):
        """Display invoice summary for this member"""
        if not SAFA_SYSTEM_AVAILABLE:
            return "SAFA system not available"
        
        try:
            invoices = []
            if hasattr(obj, 'player_invoices'):
                invoices.extend(obj.player_invoices.all())
            if hasattr(obj, 'official_invoices'):
                invoices.extend(obj.official_invoices.all())
            
            if not invoices:
                return "No invoices found"
            
            summary = []
            for invoice in invoices[:5]:  # Show max 5 invoices
                status_color = {
                    'PAID': 'green',
                    'PENDING': 'orange', 
                    'OVERDUE': 'red'
                }.get(invoice.status, 'black')
                
                total_amount = getattr(invoice, 'total_amount', getattr(invoice, 'amount', 0))
                
                summary.append(
                    f'<div style="margin: 2px 0;">'
                    f'<strong>{invoice.invoice_number}</strong>: '
                    f'R{total_amount} '
                    f'<span style="color: {status_color};">({invoice.status})</span>'
                    f'</div>'
                )
            
            return format_html(''.join(summary))
        except Exception as e:
            return f"Error loading invoices: {str(e)}"
    invoice_summary.short_description = "Invoice Summary"
    
    def outstanding_amount_display(self, obj):
        """Display total outstanding amount"""
        if not SAFA_SYSTEM_AVAILABLE:
            return "N/A"
        
        try:
            total = Decimal('0.00')
            if hasattr(obj, 'player_invoices'):
                outstanding = obj.player_invoices.filter(status__in=['PENDING', 'OVERDUE']).aggregate(
                    total=models.Sum('outstanding_amount'))['total']
                if outstanding:
                    total += outstanding
            if hasattr(obj, 'official_invoices'):
                outstanding = obj.official_invoices.filter(status__in=['PENDING', 'OVERDUE']).aggregate(
                    total=models.Sum('outstanding_amount'))['total']
                if outstanding:
                    total += outstanding
            
            if total > 0:
                return format_html(f'<strong style="color: red;">R{total:,.2f}</strong>')
            return format_html('<span style="color: green;">R0.00</span>')
        except:
            return "Error"
    outstanding_amount_display.short_description = "Outstanding Amount"

    def approve_selected(self, request, queryset):
        """Approve selected members"""
        count = 0
        for member in queryset.filter(status='PENDING'):
            member.approve_membership(request.user)
            count += 1
        self.message_user(request, _('Approved {} members').format(count))
    approve_selected.short_description = _('Approve selected members')

    def reject_selected(self, request, queryset):
        """Reject selected members with a generic reason. For a custom reason, a separate form/view would be needed."""
        count = 0
        for member in queryset.filter(status='PENDING'):
            member.reject_membership(request.user, "Rejected by admin action.")
            count += 1
        self.message_user(request, _('Rejected {} members').format(count))
    reject_selected.short_description = _('Reject selected members')

    def send_welcome_emails(self, request, queryset):
        """Send welcome emails to approved members"""
        count = 0
        for member in queryset.filter(status='ACTIVE'):
            if member.email:
                # Add your email logic here
                count += 1
        self.message_user(request, _('Sent welcome emails to {} members').format(count))
    send_welcome_emails.short_description = _('Send welcome emails')
    
    def generate_safa_invoices(self, request, queryset):
        """Generate SAFA invoices for selected members"""
        if not SAFA_SYSTEM_AVAILABLE:
            messages.error(request, "SAFA invoice system not available. Please run migrations first.")
            return
        
        count = 0
        errors = []
        
        for member in queryset:
            try:
                # Try to create invoice for player
                if hasattr(member, 'player_ptr'):
                    invoice = SAFAInvoiceManager.create_member_invoice(member)
                    count += 1
                # Try to create invoice for official
                elif hasattr(member, 'official_ptr'):
                    invoice = SAFAInvoiceManager.create_member_invoice(member)
                    count += 1
            except Exception as e:
                errors.append(f"{member.get_full_name()}: {str(e)}")
        
        if count > 0:
            messages.success(request, f"Generated {count} SAFA invoices.")
        if errors:
            messages.warning(request, f"Errors: {'; '.join(errors[:3])}")
    generate_safa_invoices.short_description = "Generate SAFA invoices for selected members"
    
    def send_payment_reminders(self, request, queryset):
        """Send payment reminders for unpaid invoices"""
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
    send_payment_reminders.short_description = _('Send payment reminder email to selected members')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user

        if user.is_superuser or user.role == 'ADMIN_NATIONAL':
            return qs
        elif user.role == 'ADMIN_PROVINCE' and user.province:
            return qs.filter(province=user.province)
        elif user.role == 'ADMIN_REGION' and user.region:
            return qs.filter(region=user.region)
        elif user.role == 'ADMIN_LOCAL_FED' and user.local_federation:
            return qs.filter(lfa=user.local_federation)
        elif user.role == 'CLUB_ADMIN' and user.club:
            return qs.filter(playerclubregistration__club=user.club)
        elif user.role == 'ASSOCIATION_ADMIN' and user.association:
            return qs.filter(playerclubregistration__club__association=user.association)
        return qs.none()


# Keep your existing Transfer admin
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


# Enhanced Invoice Admin
class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('description', 'quantity', 'unit_price', 'sub_total')
    readonly_fields = ('sub_total',)


@admin.register(Invoice)
class EnhancedInvoiceAdmin(admin.ModelAdmin):
    """Enhanced invoice admin with SAFA integration"""
    
    list_display = (
        'invoice_number', 'billed_to', 'season_display', 'invoice_type',
        'total_amount_display', 'paid_amount_display', 'payment_percentage_display', 
        'status', 'due_date', 'is_overdue'
    )
    search_fields = (
        'invoice_number',
        'player__first_name', 'player__last_name',
        'club__name',
        'official__first_name', 'official__last_name',
        'association__name',
        'vendor__name'
    )
    list_filter = ('status', 'invoice_type', 'due_date')
    date_hierarchy = 'issue_date'
    readonly_fields = ('invoice_number', 'uuid', 'is_paid', 'is_overdue', 'created', 'modified')
    
    if SAFA_SYSTEM_AVAILABLE:
        readonly_fields += ('vat_amount', 'total_amount', 'outstanding_amount', 'payment_percentage_display')
    
    actions = ['mark_as_paid_action', 'send_payment_reminder']
    inlines = [InvoiceItemInline]
    
    fieldsets = [
        (None, {
            'fields': ('invoice_number', 'uuid', 'status', 'invoice_type')
        }),
        (_('Billing To'), {
            'fields': ('player', 'club', 'official', 'association', 'vendor')
        }),
        (_('Financials'), {
            'fields': ('amount', 'paid_amount', 'tax_amount', 'payment_method', 'payment_reference')
        }),
        (_('Dates'), {
            'fields': ('issue_date', 'due_date', 'payment_date')
        }),
        (_('Administration'), {
            'fields': ('issued_by', 'notes')
        }),
        (_('System Information'), {
            'fields': ('is_paid', 'is_overdue', 'created', 'modified'),
            'classes': ('collapse',)
        })
    ]
    
    if SAFA_SYSTEM_AVAILABLE:
        fieldsets.insert(1, ('Season Information', {
            'fields': ('season_config',),
        }))
        fieldsets[3] = (_('Financials'), {
            'fields': ('subtotal', 'vat_rate', 'vat_amount', 'total_amount', 'paid_amount', 'outstanding_amount')
        })
    
    def billed_to(self, obj):
        """Display the primary entity this invoice is billed to."""
        if obj.player:
            return f"Player: {obj.player}"
        if obj.club:
            return f"Club: {obj.club}"
        if obj.official:
            return f"Official: {obj.official}"
        if obj.association:
            return f"Association: {obj.association}"
        if obj.vendor:
            return f"Vendor: {obj.vendor}"
        return "N/A"
    billed_to.short_description = _('Billed To')
    
    def season_display(self, obj):
        if SAFA_SYSTEM_AVAILABLE and hasattr(obj, 'season_config') and obj.season_config:
            return obj.season_config.season_year
        return "N/A"
    season_display.short_description = "Season"
    
    def total_amount_display(self, obj):
        if SAFA_SYSTEM_AVAILABLE and hasattr(obj, 'total_amount'):
            return f"R{obj.total_amount:,.2f}"
        return f"R{obj.amount:,.2f}"
    total_amount_display.short_description = "Total Amount"
    
    def paid_amount_display(self, obj):
        paid = getattr(obj, 'paid_amount', Decimal('0.00'))
        if paid > 0:
            return format_html('<strong style="color: green;">R{:,.2f}</strong>', paid)
        return f"R{paid:,.2f}"
    paid_amount_display.short_description = "Paid Amount"
    
    def payment_percentage_display(self, obj):
        if SAFA_SYSTEM_AVAILABLE and hasattr(obj, 'payment_percentage'):
            percentage = obj.payment_percentage
        else:
            total = getattr(obj, 'total_amount', getattr(obj, 'amount', Decimal('0.00')))
            paid = getattr(obj, 'paid_amount', Decimal('0.00'))
            percentage = (paid / total * 100) if total > 0 else 0
        
        if percentage >= 100:
            color = "green"
        elif percentage >= 50:
            color = "orange"
        else:
            color = "red"
        return format_html('<span style="color: {};">{:.1f}%</span>', color, percentage)
    payment_percentage_display.short_description = "Payment %"
    
    def mark_as_paid_action(self, request, queryset):
        """Bulk action: Mark selected invoices as paid."""
        paid_count = 0
        for invoice in queryset:
            if invoice.status != 'PAID':
                if SAFA_SYSTEM_AVAILABLE and hasattr(invoice, 'add_payment'):
                    try:
                        remaining = invoice.outstanding_amount
                        invoice.add_payment(remaining, 'MANUAL', f'Marked as paid by {request.user}')
                        paid_count += 1
                    except Exception as e:
                        messages.error(request, f"Error processing invoice {invoice.invoice_number}: {str(e)}")
                else:
                    invoice.mark_as_paid()
                    paid_count += 1
        self.message_user(request, f"{paid_count} invoice(s) marked as paid.")
    mark_as_paid_action.short_description = "Mark selected invoices as paid"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role in ['ADMIN_NATIONAL', 'ADMIN_NATIONAL_ACCOUNTS']:
            return qs
        return qs.none()


# Keep your existing admin registrations
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


@admin.register(MembershipApplication)
class MembershipApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'member', 'get_first_name', 'get_last_name', 'get_email', 'get_phone_number',
        'get_id_number', 'get_passport_number', 'club', 'status', 'submitted_at', 'reviewed_by', 'reviewed_at'
    )
    list_filter = ('status', 'club', 'submitted_at')
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
            if request.user.is_superuser or getattr(request.user, 'role', None) == 'ADMIN_NATIONAL':
                app.status = 'APPROVED'
                app.reviewed_by = request.user
                app.reviewed_at = timezone.now()
                app.save()  
    approve_applications.short_description = "Approve selected applications"

    def reject_applications(self, request, queryset):
        for app in queryset:
            if request.user.is_superuser or getattr(request.user, 'role', None) == 'ADMIN_NATIONAL':
                app.status = 'REJECTED'
                app.reviewed_by = request.user
                app.reviewed_at = timezone.now()
                app.save()
    reject_applications.short_description = "Reject selected applications"

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


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'description', 'quantity', 'unit_price', 'sub_total')
    search_fields = ('invoice__invoice_number', 'description')
    autocomplete_fields = ['invoice']
    readonly_fields = ('sub_total',)

    def sub_total(self, obj):
        return f"R{obj.sub_total:.2f}"
    sub_total.short_description = "Sub Total"


# Inlines for existing models
class PlayerClubRegistrationInline(admin.TabularInline):
    model = PlayerClubRegistration
    extra = 0
    fields = ('player', 'status', 'registration_date', 'position', 'jersey_number')
    readonly_fields = ('player', 'registration_date')
    raw_id_fields = ('player',)


class OfficialInline(admin.TabularInline):
    model = Official
    fk_name = 'association' # Specify the foreign key to use
    extra = 0
    fields = ('get_full_name', 'email', 'position', 'is_approved')
    readonly_fields = ('get_full_name', 'email', 'position', 'is_approved')
    can_delete = False
    show_change_link = True
    
    def get_queryset(self, request):
        return super().get_queryset(request).all()


# ============================================================================
# ADMIN SITE REGISTRATION AND CLEANUP
# ============================================================================

# Unregister existing models to avoid conflicts
models_to_unregister = [Member]
for model in models_to_unregister:
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass

# Register enhanced admins
admin.site.register(Member, NewMemberAdmin)

# Register remaining models
admin.site.register(TransferAppeal)
admin.site.register(Membership)

# Customize admin site
admin.site.site_header = "SAFA Financial Administration"
admin.site.site_title = "SAFA Finance Portal" 
admin.site.index_title = "Welcome to SAFA Financial Administration"

# Add custom admin views if needed
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


# Additional SAFA Payment models if available
if SAFA_SYSTEM_AVAILABLE:
    try:
        @admin.register(InvoicePayment)
        class InvoicePaymentAdmin(SAFAAccountsAdminMixin, admin.ModelAdmin):
            list_display = ['invoice', 'amount_display', 'payment_method', 'payment_date', 'status', 'processed_by']
            list_filter = ['payment_method', 'status', 'payment_date']
            search_fields = ['invoice__invoice_number', 'payment_reference']
            readonly_fields = ['processed_by']
            
            def amount_display(self, obj):
                return f"R{obj.amount:,.2f}"
            amount_display.short_description = "Amount"

        @admin.register(InvoiceNote)
        class InvoiceNoteAdmin(SAFAAccountsAdminMixin, admin.ModelAdmin):
            list_display = ['invoice', 'note_type', 'subject', 'is_internal', 'created_by', 'created']
            list_filter = ['note_type', 'is_internal', 'created']
            search_fields = ['invoice__invoice_number', 'subject', 'content']
            readonly_fields = ['created_by']

    except Exception as e:
        print(f"⚠️ Could not register SAFA payment models: {e}")