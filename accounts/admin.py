import collections
import sys

# Fix for collections.Iterator removed in Python 3.10
if sys.version_info >= (3, 10) and not hasattr(collections, 'Iterator'):
    collections.Iterator = collections.abc.Iterator

from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# Update imports to include new models
from .models import CustomUser, ModelWithLogo, Position, OrganizationType, DocumentAccessLog
from membership.models import Member

class PlayerInline(admin.TabularInline):
    model = Member
    fk_name = "user"
    extra = 0
    fields = ['first_name', 'last_name', 'safa_id', 'status']
    verbose_name = "Player"
    verbose_name_plural = "Players"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(role='PLAYER')

class OfficialInline(admin.TabularInline):
    model = Member
    fk_name = "user"
    extra = 0
    fields = ['first_name', 'last_name', 'safa_id', 'status']
    verbose_name = "Official"
    verbose_name_plural = "Officials"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(role='OFFICIAL')


# Import directly from geography models
try:
    from geography.models import Province, Region, LocalFootballAssociation, Club, NationalFederation
except (ImportError, RuntimeError):
    Province = None
    Region = None
    LocalFootballAssociation = None
    Club = None
    NationalFederation = None

# Properly import Province directly
try:
    from geography.models import Province
    PROVINCE_QUERYSET = Province.objects.all()
except (ImportError, RuntimeError):
    from django.db.models.query import EmptyQuerySet
    PROVINCE_QUERYSET = EmptyQuerySet()

# Create a custom ModelForm specifically for admin use
class CustomUserAdminForm(forms.ModelForm):
    # Add a ModelChoiceField for province that maps to province_id - fix the queryset issue
    province = forms.ModelChoiceField(
        queryset=PROVINCE_QUERYSET,
        required=False,
        label="Province"
    )
    
    class Meta:
        model = CustomUser
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If we're editing an existing user, set the province field value
        if self.instance and self.instance.pk and self.instance.province_id:
            try:
                province = Province.objects.get(pk=self.instance.province_id)
                self.initial['province'] = province
            except:
                pass

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Map the province field to province_id when saving
        if 'province' in self.cleaned_data and self.cleaned_data['province']:
            user.province_id = self.cleaned_data['province'].id
            
        if commit:
            user.save()
            
        return user

class CustomUserCreationForm(forms.ModelForm):
    """Form for creating new users in the admin. Includes password fields."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('email', 'role', 'first_name', 'last_name')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class CustomUserChangeForm(forms.ModelForm):
    """Form for updating users in the admin. Includes all fields but
    replaces the password field with a password hash display field."""
    password = ReadOnlyPasswordHashField(
        label=_("Password"),
        help_text=_("Raw passwords are not stored, so there is no way to see this "
                    "user's password, but you can change the password using "
                    "<a href=\"../password/\">this form</a>.")
    )

    class Meta:
        model = CustomUser
        fields = '__all__'

    def clean_password(self):
        # Return the initial value regardless of what the user provides
        return self.initial.get('password', '')

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['title', 'display_levels', 'employment_type', 'is_active', 'requires_approval', 'created_by', 'created_at']
    list_filter = ['employment_type', 'is_active', 'requires_approval']
    search_fields = ['title', 'description', 'levels']
    actions = ['approve_positions', 'activate_positions', 'make_available_all_levels']
    
    def display_levels(self, obj):
        """Format the levels for display in admin"""
        if not obj.levels:
            return "None"
        levels = obj.levels.split(',')
        return ', '.join(levels)
    display_levels.short_description = 'Available at Levels'
    
    def make_available_all_levels(self, request, queryset):
        """Make selected positions available at all levels"""
        all_levels = 'NATIONAL,PROVINCE,REGION,LFA,CLUB'
        updated = queryset.update(levels=all_levels)
        self.message_user(request, f'{updated} positions updated to be available at all levels.')
    
    def approve_positions(self, request, queryset):
        updated = queryset.update(requires_approval=False)
        self.message_user(request, f'{updated} positions approved.')
    
    def activate_positions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} positions activated.')
    
    def duplicate_positions(self, request, queryset):
        """Duplicate positions for different levels"""
        duplicated = 0
        for position in queryset:
            # This method is now obsolete as positions can be available at multiple levels
            # Just update the levels field to include all levels
            position.levels = 'NATIONAL,PROVINCE,REGION,LFA,CLUB'
            position.save()
            duplicated += 1
        
        self.message_user(request, f'{duplicated} positions duplicated across different levels.')
    
    duplicate_positions.short_description = "Duplicate positions to other levels"

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    
    list_display = [
        'email', 'get_full_name', 'role', 'get_organization', 'display_position', 'popi_act_consent',
        'id_document_type', 'id_number', 'passport_number', 'id_number_other',
        'membership_status',  'safa_id', 'is_active', 'date_joined'
    ]
    
    list_filter = [
        'role', 'popi_act_consent', 'membership_status', 
        'is_active', 'is_staff', 'date_joined', 'association'
    ]
    
    search_fields = ['email', 'first_name', 'last_name', 'id_number', 'safa_id']
    ordering = ['email']
    
    actions = ['activate_users', 'deactivate_users']
    inlines = [PlayerInline, OfficialInline]

    def display_position(self, obj):
        # Safely access the user's position through their member profile
        try:
            if hasattr(obj, 'member_profile') and obj.member_profile and hasattr(obj.member_profile, 'profile') and obj.member_profile.profile:
                if obj.member_profile.profile.official_position:
                    return obj.member_profile.profile.official_position.title
        except Exception:
            return "N/A"
        return "N/A"
    display_position.short_description = 'Position'
    
    def activate_users(self, request, queryset):
        """Admin action to activate selected users"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users have been activated.')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        """Admin action to deactivate selected users"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users have been deactivated.')
    deactivate_users.short_description = "Deactivate selected users"
    
    # Fix the fieldsets to include all document fields and pictures
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'date_of_birth', 'gender', 'profile_picture')}),
        ('SAFA Structure', {
            'fields': (
                'role',
                'national_federation', 'province', 'region', 'local_federation', 'association', 'club',
            )
        }),
        ('Identification', {
            'fields': (
                'id_document_type', 'id_number', 'passport_number', 
                'id_number_other', 'id_document', 
                'popi_act_consent'
            )
        }),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('SAFA Info', {'fields': ('safa_id', 'fifa_id', 'membership_status')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    
    def activate_membership(self, request, queryset):
        """Activate selected memberships and generate SAFA IDs"""
        from membership.models import Invoice # Import Invoice model
        activated_count = 0
        skipped_count = 0
        for user in queryset.filter(membership_status='PENDING'):
            # Check if there's a paid invoice for this user
            # Assuming a user has one primary invoice for their membership registration
            invoice = Invoice.objects.filter(member__user=user, invoice_type='REGISTRATION', status='PAID').first()

            if invoice and invoice.is_paid:
                user.membership_status = 'ACTIVE'
                user.membership_approved_date = timezone.now()
                
                # Generate clean SAFA ID without random/PROV
                if hasattr(user, 'member_profile') and user.member_profile and not user.member_profile.safa_id:
                    user.member_profile.generate_safa_id()
                    user.safa_id = user.member_profile.safa_id
                    user.member_profile.save()
                
                user.save()
                activated_count += 1
                
                # Create digital card automatically
                from membership_cards.models import DigitalCard
                try:
                    DigitalCard.objects.get_or_create(
                        user=user,
                        defaults={
                            'expires_date': timezone.now().date() + timezone.timedelta(days=365),
                            'status': 'ACTIVE'
                        }
                    )
                except:
                    pass
            else:
                skipped_count += 1
                self.message_user(request, f"Membership for {user.get_full_name()} (SAFA ID: {user.safa_id or 'N/A'}) cannot be activated. Payment not yet verified.", messages.WARNING)
        
        if activated_count > 0:
            self.message_user(
                request,
                f'{activated_count} memberships activated and SAFA IDs generated',
                messages.SUCCESS
            )
        if skipped_count > 0:
            self.message_user(
                request,
                f'{skipped_count} memberships skipped due to unverified payment.',
                messages.WARNING
            )
    activate_membership.short_description = "Activate selected memberships"
    
    def suspend_membership(self, request, queryset):
        """Admin action to suspend memberships"""
        updated = queryset.update(membership_status='SUSPENDED')
        self.message_user(
            request,
            f'{updated} membership(s) successfully suspended.',
            messages.WARNING
        )
    suspend_membership.short_description = "Suspend selected memberships"

    def mark_payment_received(self, request, queryset):
        """Admin action to mark payment as received"""
        from django.utils import timezone
        updated = 0
        for user in queryset.filter(membership_status='PENDING'):
            user.membership_status = 'PAID'
            user.membership_paid_date = timezone.now()
            user.save()
            updated += 1
        
        self.message_user(
            request,
            f'{updated} payment(s) marked as received.',
            messages.SUCCESS
        )
    mark_payment_received.short_description = "Mark payment as received"

    actions = [
        'activate_users', 'deactivate_users', 
        'mark_payment_received', 'activate_membership', 'suspend_membership',
        'generate_safa_ids'  # Add this action back
    ]
    
    def generate_safa_ids(self, request, queryset):
        """Generate SAFA IDs for selected users"""
        generated_count = 0
        for user in queryset.filter(safa_id__isnull=True):
            member_profile, created = Member.objects.get_or_create(user=user)
            member_profile.generate_safa_id()
            user.safa_id = member_profile.safa_id
            member_profile.save()
            user.save()
            generated_count += 1
        
        self.message_user(
            request,
            f'{generated_count} SAFA IDs generated successfully.',
            messages.SUCCESS
        )
    generate_safa_ids.short_description = "Generate SAFA IDs for selected users"

    def get_organization(self, obj):
        """Display organization based on role, including Region Admins and Association Admins"""
        try:
            if obj.role == 'ADMIN_NATIONAL':
                if obj.national_federation:
                    return f"National: {obj.national_federation.name}"
                return "National: SAFA"
            elif obj.role == 'ADMIN_NATIONAL_ACCOUNTS':
                if obj.national_federation:
                    return f"National Accounts: {obj.national_federation.name}"
                return "National Accounts: SAFA"
            elif obj.role == 'ADMIN_PROVINCE':
                if obj.province:
                    return f"Province: {obj.province.name}"
                return "Province: Not Set"
            elif obj.role == 'ADMIN_REGION':
                if obj.region:
                    return f"Region: {obj.region.name}"
                return "Region: Not Set"
            elif obj.role == 'ADMIN_LOCAL_FED':
                if obj.local_federation:
                    return f"LFA: {obj.local_federation.name}"
                return "LFA: Not Set"
            elif obj.role == 'CLUB_ADMIN':
                if obj.club:
                    return f"Club: {obj.club.name}"
                return "Club: Not Set"
            elif obj.role == 'ASSOCIATION_ADMIN':
                if obj.association:
                    return f"Association: {obj.association.name}"
                return "Association: Not Set"
            # Also display association for any user that has an association set
            elif obj.association:
                return f"Association: {obj.association.name}"
            return "Not Assigned"
        except Exception as e:
            return f"Error: {str(e)}"
    
    get_organization.short_description = 'Organization'

# Add OrganizationType admin
@admin.register(OrganizationType)
class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'is_active', 'requires_approval']
    list_filter = ['level', 'is_active', 'requires_approval']
    search_fields = ['name']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Display all positions regardless of level - this supports the new levels field
        # which can include multiple levels (NATIONAL,PROVINCE,REGION,LFA,CLUB,ASSOCIATION)
        if db_field.name == "position":
            kwargs["queryset"] = Position.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)



"""
# This section is commented out as Membership model is not available

class MembershipAdmin(admin.ModelAdmin):
    # Admin configuration for the Membership model.
    list_display = ('user', 'membership_type', 'start_date', 'end_date', 'is_active', 'payment_confirmed')
    list_filter = ('membership_type', 'is_active', 'payment_confirmed', 'start_date')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'user__safa_id')
    
    fieldsets = (
        (_('Membership Details'), {
            'fields': ('user', 'membership_type', 'start_date', 'end_date', 'is_active')
        }),
        (_('Organization'), {
            'fields': ('club', 'association', 'national_federation', 'region', 'local_football_association')
        }),
        (_('Payment'), {
            'fields': ('payment_confirmed', 'payment_date')
        }),
        (_('Player Details'), {
            'fields': ('player_category', 'jersey_number', 'position'),
            'classes': ('collapse',)
        }),
        (_('Contact Info'), {
            'fields': ('address', 'postal_address', 'next_of_kin'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['confirm_payments', 'activate_memberships', 'deactivate_memberships']
    
    def confirm_payments(self, request, queryset):
        # Confirm payments for selected memberships
        from django.utils import timezone
        count = queryset.filter(payment_confirmed=False).update(
            payment_confirmed=True,
            payment_date=timezone.now()
        )
        self.message_user(request, _(f"Confirmed payments for {count} memberships."))
    confirm_payments.short_description = _("Confirm payments for selected memberships")
    
    def activate_memberships(self, request, queryset):
        # Activate selected memberships
        queryset.update(is_active=True)
    activate_memberships.short_description = _("Activate selected memberships")
    
    def deactivate_memberships(self, request, queryset):
        # Deactivate selected memberships
        queryset.update(is_active=False)
    deactivate_memberships.short_description = _("Deactivate selected memberships")

# admin.site.register(Membership, MembershipAdmin)
"""

@admin.register(DocumentAccessLog)
class DocumentAccessLogAdmin(admin.ModelAdmin):
    """Admin interface for Document Access Logs"""
    list_display = [
        'access_time', 'user', 'document_name', 'document_owner', 'action', 
        'document_type', 'formatted_file_size', 'watermarked', 'success', 'ip_address'
    ]
    list_filter = [
        'action', 'document_type', 'watermarked', 'success', 'access_time',
        'user__role'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name', 
        'document_name', 'document_owner', 'ip_address'
    ]
    readonly_fields = [
        'user', 'document_type', 'document_name', 'document_owner', 
        'action', 'access_time', 'ip_address', 'user_agent', 'file_size',
        'watermarked', 'success', 'notes'
    ]
    ordering = ['-access_time']
    date_hierarchy = 'access_time'
    
    fieldsets = (
        ('Document Access Information', {
            'fields': ('user', 'document_type', 'document_name', 'document_owner', 'action')
        }),
        ('Access Details', {
            'fields': ('access_time', 'ip_address', 'user_agent', 'file_size')
        }),
        ('Security', {
            'fields': ('watermarked', 'success', 'notes')
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent manual creation of access logs"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make logs read-only"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion only for superusers"""
        return request.user.is_superuser
    
    def get_queryset(self, request):
        """Filter logs based on user role"""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        # Club admins can only see logs for their club's documents
        if request.user.role == 'CLUB_ADMIN' and request.user.club:
            return qs.filter(user__club=request.user.club)
        
        # LFA admins can see logs for their LFA
        if request.user.role == 'ADMIN_LOCAL_FED' and request.user.local_federation:
            return qs.filter(user__local_federation=request.user.local_federation)
        
        # Regional admins can see logs for their region
        if request.user.role == 'ADMIN_REGION' and request.user.region:
            return qs.filter(user__region=request.user.region)
        
        # Provincial admins can see logs for their province
        if request.user.role == 'ADMIN_PROVINCE' and request.user.province:
            return qs.filter(user__province=request.user.province)
        
        # National admins can see all logs
        if request.user.role == 'ADMIN_COUNTRY':
            return qs
        
        # Default: no access
        return qs.none()

# admin.site.register(Membership, MembershipAdmin)