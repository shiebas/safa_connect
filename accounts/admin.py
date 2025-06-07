import collections
import sys

# Fix for collections.Iterator removed in Python 3.10
if sys.version_info >= (3, 10) and not hasattr(collections, 'Iterator'):
    collections.Iterator = collections.abc.Iterator

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import gettext_lazy as _

# Fix import statement - update model names to match what's actually defined in models.py
from .models import CustomUser, ModelWithLogo, RegistrationType

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
        fields = ('email', 'role', 'first_name', 'last_name', 'name', 'surname')

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

class CustomUserAdmin(UserAdmin):
    """Admin configuration for the CustomUser model."""
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'safa_id', 'fifa_id')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'role')
    search_fields = ('email', 'first_name', 'last_name', 'name', 'surname', 'safa_id', 'fifa_id')
    ordering = ('email',)
    
    # Admin is divided into different sections for better organization
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Information'), {
            'fields': ('first_name', 'last_name', 'name', 'middle_name', 'surname', 'alias',
                      'date_of_birth', 'gender', 'country_code', 'id_number', 'id_number_other',
                      'passport_number', 'id_document_type', 'id_document')
        }),
        (_('Role & Status'), {
            'fields': ('role', 'registration_type', 'is_active', 'is_staff', 'is_superuser',
                      'membership_card', 'payment_required', 'safa_id', 'fifa_id')
        }),
        (_('Administrative Relationship'), {
            'fields': ('province_id', 'region_id', 'local_federation_id', 'club_id')
        }),
        (_('Media'), {
            'fields': ('profile_photo', 'logo')
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'registration_date')}),
    )
    
    # Fields shown when creating a new user through admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'first_name', 'last_name'),
        }),
    )
    
    # Actions available in the admin
    actions = ['activate_users', 'deactivate_users', 'generate_safa_ids', 'fetch_fifa_ids']
    
    def activate_users(self, request, queryset):
        """Activate selected users"""
        queryset.update(is_active=True)
    activate_users.short_description = _("Activate selected users")
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        queryset.update(is_active=False)
    deactivate_users.short_description = _("Deactivate selected users")
    
    def generate_safa_ids(self, request, queryset):
        """Generate SAFA IDs for selected users without IDs"""
        count = 0
        for user in queryset.filter(safa_id__isnull=True):
            user.generate_safa_id()
            user.save()
            count += 1
        self.message_user(request, _(f"Generated SAFA IDs for {count} users."))
    generate_safa_ids.short_description = _("Generate SAFA IDs for selected users")
    
    def fetch_fifa_ids(self, request, queryset):
        """Fetch FIFA IDs for selected users"""
        count = 0
        for user in queryset.filter(fifa_id__isnull=True):
            user.fetch_fifa_id_from_api(api_key="dummy-key")  # Replace with actual API key
            count += 1
        self.message_user(request, _(f"Generated FIFA IDs for {count} users."))
    fetch_fifa_ids.short_description = _("Generate/Fetch FIFA IDs for selected users")

class RegistrationTypeAdmin(admin.ModelAdmin):
    """Admin configuration for the RegistrationType model."""
    list_display = ('name', 'allowed_user_roles')
    search_fields = ('name', 'allowed_user_roles')

# Register models with the admin site
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(RegistrationType, RegistrationTypeAdmin)

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