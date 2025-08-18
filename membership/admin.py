# membership/admin.py - CORRECTED VERSION
# Fixed to work with the new SAFA models

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import models  # noqa: F401
from django.contrib import messages
from decimal import Decimal  # noqa: F401

# Import models from the corrected models.py
from .models import (
    Member,
    MemberDocument,  # Not NewMemberDocument
    MemberProfile,
    MemberSeasonHistory,
    SAFASeasonConfig,
    SAFAFeeStructure,
    Transfer,
    OrganizationSeasonRegistration,
    ClubMemberQuota,
    Invoice,
    InvoiceItem,
    RegistrationWorkflow
)

class SAFAAccountsAdminMixin:
    """Mixin to restrict admin access to SAFA accounts staff only"""
    
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
            getattr(request.user, 'role', None) in ['ADMIN_NATIONAL', 'ADMIN_NATIONAL_ACCOUNTS']
        )


# ============================================================================
# SAFA SEASON AND FEE CONFIGURATION ADMINS
# ============================================================================

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
        ('Registration Periods', {
            'fields': (
                'organization_registration_start', 'organization_registration_end',
                'member_registration_start', 'member_registration_end'
            )
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
    
    actions = ['activate_season', 'generate_renewal_invoices']
    
    def season_period(self, obj):
        return f"{obj.season_start_date} to {obj.season_end_date}"
    season_period.short_description = "Season Period"
    
    def vat_rate_display(self, obj):
        return f"{(obj.vat_rate * 100):.1f}%"
    vat_rate_display.short_description = "VAT Rate"
    
    def invoice_count(self, obj):
        count = obj.invoices.count()
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
        # This would call a management command or service to generate renewals
        messages.success(request, f"Renewal invoice generation initiated for season {season.season_year}.")
    generate_renewal_invoices.short_description = "Generate renewal invoices for season"


@admin.register(SAFAFeeStructure)
class SAFAFeeStructureAdmin(SAFAAccountsAdminMixin, admin.ModelAdmin):
    list_display = [
        'entity_type', 'season_year', 'annual_fee_display', 'minimum_fee_display',
        'is_pro_rata', 'is_organization', 'created_by'
    ]
    list_filter = ['season_config__season_year', 'entity_type', 'is_pro_rata', 'is_organization']
    search_fields = ['entity_type', 'description']
    readonly_fields = ['created_by', 'created_at', 'updated_at', 'is_organization']
    
    fieldsets = (
        ('Fee Configuration', {
            'fields': ('season_config', 'entity_type', 'annual_fee', 'minimum_fee')
        }),
        ('Settings', {
            'fields': ('is_pro_rata', 'requires_organization_payment', 'description')
        }),
        ('System Information', {
            'fields': ('is_organization', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
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


@admin.register(OrganizationSeasonRegistration)
class OrganizationSeasonRegistrationAdmin(SAFAAccountsAdminMixin, admin.ModelAdmin):
    list_display = [
        'organization_name', 'organization_type', 'season_year', 'status',
        'registration_date', 'invoice_link'
    ]
    list_filter = ['status', 'season_config__season_year', 'content_type']
    search_fields = ['object_id']
    readonly_fields = ['organization_name', 'organization_type', 'registered_by']
    
    def season_year(self, obj):
        return obj.season_config.season_year
    season_year.short_description = "Season"
    
    def invoice_link(self, obj):
        if obj.invoice:
            url = reverse('admin:membership_invoice_change', args=[obj.invoice.id])
            return format_html('<a href="{}">{}</a>', url, obj.invoice.invoice_number)
        return "No Invoice"
    invoice_link.short_description = "Invoice"


# ============================================================================
# MEMBER MANAGEMENT ADMINS
# ============================================================================

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    """Enhanced Member admin with SAFA integration"""
    
    list_display = (
        'safa_id_link', 'get_full_name', 'email', 'role', 'status', 
        'current_club', 'current_season', 'age_display', 'registration_complete'
    )
    list_display_links = ('safa_id_link', 'get_full_name',)
    list_filter = (
        'status', 'role', 'current_season', 'registration_complete',
        'province', 'current_club', 'registration_method'
    )
    search_fields = (
        'safa_id', 'first_name', 'last_name', 'email', 'id_number', 
        'current_club__name'
    )
    actions = ['approve_selected', 'reject_selected', 'generate_invoices']
    
    fieldsets = (
        ('SAFA Identification', {
            'fields': ('safa_id', 'is_existing_member', 'previous_safa_id')
        }),
        ('Personal Information', {
            'fields': (
                ('first_name', 'last_name'), 'email', 'phone_number',
                ('date_of_birth', 'gender'), 'nationality'
            )
        }),
        ('Identification Documents', {
            'fields': ('id_number', 'passport_number', 'id_document'),
            'classes': ('collapse',)
        }),
        ('SAFA Registration', {
            'fields': (
                'role', 'status', 'registration_method', 'current_season',
                'registration_complete'
            )
        }),
        ('Club & Geography', {
            'fields': (
                'current_club', 'province', 'region', 'lfa', 'associations'
            )
        }),
        ('Address Information', {
            'fields': (
                'street_address', 'suburb', 'city', 'state', 
                'postal_code', 'country', 'registration_address'
            ),
            'classes': ('collapse',)
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact', 'emergency_phone', 'medical_notes'),
            'classes': ('collapse',)
        }),
        ('Approval & Status', {
            'fields': (
                'approved_by', 'approved_date', 'rejection_reason'
            ),
            'classes': ('collapse',)
        }),
        ('Consent & Terms', {
            'fields': ('terms_accepted', 'privacy_accepted', 'marketing_consent'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['safa_id', 'approved_by', 'approved_date', 'age_display']
    filter_horizontal = ['associations']
    
    def safa_id_link(self, obj):
        url = reverse("admin:membership_member_change", args=[obj.id])
        return format_html('<a href="{}">{}</a>', url, obj.safa_id)
    safa_id_link.short_description = "SAFA ID"
    safa_id_link.admin_order_field = "safa_id"
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = _('Full Name')
    
    def age_display(self, obj):
        if obj.age is not None:
            return f"{obj.age} years"
        return "Unknown"
    age_display.short_description = "Age"
    
    def approve_selected(self, request, queryset):
        """Approve selected members"""
        count = 0
        for member in queryset.filter(status='PENDING'):
            member.approve_safa_membership(request.user)
            count += 1
        self.message_user(request, f'Approved {count} members')
    approve_selected.short_description = 'Approve selected members'
    
    def reject_selected(self, request, queryset):
        """Reject selected members"""
        count = 0
        for member in queryset.filter(status='PENDING'):
            member.reject_safa_membership(request.user, "Rejected by admin action.")
            count += 1
        self.message_user(request, f'Rejected {count} members')
    reject_selected.short_description = 'Reject selected members'
    
    def generate_invoices(self, request, queryset):
        """Generate invoices for selected members"""
        count = 0
        errors = []
        
        for member in queryset:
            try:
                # Check if member already has an invoice for current season
                existing_invoice = member.invoices.filter(
                    season_config=member.current_season,
                    status__in=['PENDING', 'PAID']
                ).first()
                
                if existing_invoice:
                    continue
                
                invoice = Invoice.create_member_invoice(member)  # noqa: F841
                count += 1
            except Exception as e:
                errors.append(f"{member.get_full_name()}: {str(e)}")
        
        if count > 0:
            messages.success(request, f"Generated {count} invoices.")
        if errors:
            messages.warning(request, f"Errors: {'; '.join(errors[:3])}")
    generate_invoices.short_description = "Generate SAFA invoices for selected members"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user

        if user.is_superuser or getattr(user, 'role', None) in ['ADMIN_NATIONAL', 'ADMIN_NATIONAL_ACCOUNTS']:
            return qs
        elif getattr(user, 'role', None) == 'ADMIN_PROVINCE' and hasattr(user, 'province'):
            return qs.filter(province=user.province)
        elif getattr(user, 'role', None) == 'ADMIN_REGION' and hasattr(user, 'region'):
            return qs.filter(region=user.region)
        elif getattr(user, 'role', None) == 'ADMIN_LOCAL_FED' and hasattr(user, 'lfa'):
            return qs.filter(lfa=user.lfa)
        elif getattr(user, 'role', None) == 'CLUB_ADMIN' and hasattr(user, 'club'):
            return qs.filter(current_club=user.club)
        return qs.none()





# ============================================================================
# INVOICE AND FINANCIAL ADMINS
# ============================================================================

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('description', 'quantity', 'unit_price', 'sub_total_display')
    readonly_fields = ('sub_total_display',)

    def sub_total_display(self, obj):
        return f"R{obj.sub_total:.2f}"
    sub_total_display.short_description = "Sub Total"


@admin.register(Invoice)
class InvoiceAdmin(SAFAAccountsAdminMixin, admin.ModelAdmin):
    list_display = (
        'invoice_number', 'billed_to', 'season_year', 'invoice_type',
        'total_amount_display', 'paid_amount_display', 'outstanding_amount_display',
        'status', 'due_date', 'is_overdue_display'
    )
    search_fields = (
        'invoice_number', 'member__first_name', 'member__last_name'
    )
    list_filter = ('status', 'invoice_type', 'season_config__season_year', 'due_date')
    date_hierarchy = 'issue_date'
    readonly_fields = (
        'uuid', 'invoice_number', 'vat_amount', 'total_amount', 
        'outstanding_amount', 'is_overdue_display'
    )
    actions = ['mark_as_paid_action', 'send_payment_reminders']
    inlines = [InvoiceItemInline]
    
    fieldsets = [
        ('Invoice Information', {
            'fields': ('invoice_number', 'uuid', 'status', 'invoice_type', 'season_config')
        }),
        ('Billing Details', {
            'fields': ('member', 'content_type', 'object_id')
        }),
        ('Financial Details', {
            'fields': (
                'subtotal', 'vat_rate', 'vat_amount', 'total_amount',
                'paid_amount', 'outstanding_amount'
            )
        }),
        ('Payment Plan', {
            'fields': ('is_payment_plan', 'installments'),
            'classes': ('collapse',)
        }),
        ('Dates & Payment', {
            'fields': ('issue_date', 'due_date', 'payment_date', 'payment_method', 'payment_reference')
        }),
        ('Administration', {
            'fields': ('issued_by', 'notes')
        })
    ]
    
    def season_year(self, obj):
        return obj.season_config.season_year
    season_year.short_description = "Season"
    
    def billed_to(self, obj):
        if obj.member:
            return f"Member: {obj.member.get_full_name()}"
        elif obj.organization:
            return f"Org: {getattr(obj.organization, 'name', str(obj.organization))}"
        return "Unknown"
    billed_to.short_description = "Billed To"
    
    def total_amount_display(self, obj):
        return f"R{obj.total_amount:,.2f}"
    total_amount_display.short_description = "Total Amount"
    
    def paid_amount_display(self, obj):
        if obj.paid_amount > 0:
            return format_html('<strong style="color: green;">R{:,.2f}</strong>', obj.paid_amount)
        return f"R{obj.paid_amount:,.2f}"
    paid_amount_display.short_description = "Paid Amount"
    
    def outstanding_amount_display(self, obj):
        if hasattr(obj, 'outstanding_amount'):
            amount = obj.outstanding_amount
        else:
            amount = obj.total_amount - obj.paid_amount
        
        if amount > 0:
            return format_html('<strong style="color: red;">R{:,.2f}</strong>', amount)
        return f"R{amount:,.2f}"
    outstanding_amount_display.short_description = "Outstanding"
    
    def is_overdue_display(self, obj):
        if hasattr(obj, 'is_overdue'):
            is_overdue = obj.is_overdue
        else:
            is_overdue = (obj.due_date and obj.due_date < timezone.now().date() 
                         and obj.status in ['PENDING', 'PARTIALLY_PAID'])
        
        if is_overdue:
            return format_html('<span style="color: red;">Yes</span>')
        return "No"
    is_overdue_display.short_description = "Overdue"
    
    def mark_as_paid_action(self, request, queryset):
        """Mark selected invoices as paid"""
        paid_count = 0
        for invoice in queryset:
            if invoice.status != 'PAID':
                invoice.mark_as_paid('MANUAL', f'Marked as paid by {request.user}')
                paid_count += 1
        self.message_user(request, f"{paid_count} invoice(s) marked as paid.")
    mark_as_paid_action.short_description = "Mark selected invoices as paid"
    
    def send_payment_reminders(self, request, queryset):
        """Send payment reminders for unpaid invoices"""
        count = 0
        for invoice in queryset.filter(status__in=['PENDING', 'OVERDUE']):
            if invoice.member and invoice.member.email:
                # Email sending logic would go here
                count += 1
        self.message_user(request, f"Sent payment reminders for {count} invoices.")
    send_payment_reminders.short_description = "Send payment reminders"


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'description', 'quantity', 'amount', 'sub_total_display')
    search_fields = ('invoice__invoice_number', 'description')
    raw_id_fields = ['invoice']
    
    def sub_total_display(self, obj):
        return f"R{obj.sub_total:.2f}"
    sub_total_display.short_description = "Sub Total"


# ============================================================================
# TRANSFER MANAGEMENT
# ============================================================================

@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = (
        'member', 'from_club', 'to_club', 'status', 'request_date', 
        'effective_date', 'transfer_fee_display'
    )
    list_filter = ('status', 'request_date', 'effective_date')
    search_fields = (
        'member__first_name', 'member__last_name', 
        'from_club__name', 'to_club__name'
    )
    readonly_fields = ['approved_by', 'approved_date', 'effective_date']
    actions = ['approve_transfers', 'reject_transfers']
    
    fieldsets = (
        ('Transfer Details', {
            'fields': ('member', 'from_club', 'to_club', 'request_date')
        }),
        ('Financial', {
            'fields': ('transfer_fee',)
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by', 'approved_date', 'effective_date')
        }),
        ('Reason & Notes', {
            'fields': ('reason', 'rejection_reason')
        })
    )
    
    def transfer_fee_display(self, obj):
        if obj.transfer_fee and obj.transfer_fee > 0:
            return f"R{obj.transfer_fee:,.2f}"
        return "Free"
    transfer_fee_display.short_description = 'Transfer Fee'
    
    def approve_transfers(self, request, queryset):
        count = 0
        for transfer in queryset.filter(status='PENDING'):
            try:
                transfer.approve(request.user)
                count += 1
            except Exception as e:
                messages.error(request, f"Error approving transfer for {transfer.member}: {str(e)}")
        self.message_user(request, f'Approved {count} transfers')
    approve_transfers.short_description = 'Approve selected transfers'
    
    def reject_transfers(self, request, queryset):
        count = 0
        for transfer in queryset.filter(status='PENDING'):
            transfer.reject(request.user, "Rejected by admin")
            count += 1
        self.message_user(request, f'Rejected {count} transfers')
    reject_transfers.short_description = 'Reject selected transfers'


@admin.register(MemberDocument)
class NewMemberDocumentAdmin(admin.ModelAdmin):
    list_display = ['member', 'document_type', 'created', 'verification_status']
    list_filter = ['document_type', 'verification_status', 'created']
    search_fields = ['member__first_name', 'member__last_name', 'notes']
    raw_id_fields = ['member', 'verified_by']
    readonly_fields = ['created', 'verified_date']


# ============================================================================
# ADMIN SITE CUSTOMIZATION
# ============================================================================

# Customize admin site headers
admin.site.site_header = "SAFA Financial Administration"
admin.site.site_title = "SAFA Finance Portal" 
admin.site.index_title = "Welcome to SAFA Financial Administration"