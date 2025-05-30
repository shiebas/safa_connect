from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from geography.admin import ModelWithLogoAdmin
from .models import Member, Player, PlayerClubRegistration, Transfer

@admin.register(Member)
class MemberAdmin(ModelWithLogoAdmin):
    list_display = ['membership_number', 'first_name', 'last_name', 
                   'email', 'role', 'club', 'status', 'display_images']
    list_filter = ['status', 'role', 'club', 'registration_date']
    search_fields = ['first_name', 'last_name', 'email', 'membership_number']
    readonly_fields = ['display_logo_preview', 'display_profile_preview']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone_number')
        }),
        (_('Address'), {
            'fields': ('street_address', 'suburb', 'city', 'state', 
                      'postal_code', 'country')
        }),
        (_('Membership Details'), {
            'fields': ('club', 'role', 'status', 'membership_number', 
                      'date_of_birth', 'registration_date', 'expiry_date')
        }),
        (_('Images'), {
            'fields': ('logo', 'display_logo_preview', 
                      'profile_picture', 'display_profile_preview')
        }),
        (_('Emergency Information'), {
            'fields': ('emergency_contact', 'emergency_phone', 'medical_notes')
        }),
    )

    def display_images(self, obj):
        logo_img = f'<img src="{obj.logo_url}" width="30" height="30" style="margin-right: 10px;" />' if obj.logo else ''
        profile_img = f'<img src="{obj.profile_picture_url}" width="30" height="30" />' if obj.profile_picture else ''
        return format_html(f'{logo_img}{profile_img}')
    display_images.short_description = _('Images')

    def display_logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="150" height="150" />', obj.logo_url)
        return _("No logo uploaded")
    display_logo_preview.short_description = _('Logo Preview')

    def display_profile_preview(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="150" height="150" />', obj.profile_picture_url)
        return _("No profile picture uploaded")
    display_profile_preview.short_description = _('Profile Picture Preview')

@admin.register(Player)
class PlayerAdmin(MemberAdmin):
    # Inherits all from MemberAdmin since physical attributes are now in PlayerClubRegistration
    pass

@admin.register(PlayerClubRegistration)
class PlayerClubRegistrationAdmin(admin.ModelAdmin):
    list_display = ['player', 'club', 'position', 'jersey_number', 
                    'status', 'registration_date']
    list_filter = ['status', 'position', 'club', 'registration_date']
    search_fields = ['player__first_name', 'player__last_name', 
                    'player__membership_number', 'club__name']
    fieldsets = (
        (None, {
            'fields': ('player', 'club')
        }),
        (_('Registration Details'), {
            'fields': ('registration_date', 'status', 'expiry_date')
        }),
        (_('Playing Details'), {
            'fields': ('position', 'jersey_number', 'height', 'weight')
        }),
        (_('Additional Information'), {
            'fields': ('notes',)
        }),
    )

@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('player', 'from_club', 'to_club', 'request_date', 'status', 'transfer_fee')
    list_filter = ('status', 'request_date', 'from_club', 'to_club')
    search_fields = ('player__first_name', 'player__last_name', 'from_club__name', 'to_club__name')
    readonly_fields = ('approved_date', 'effective_date')
    fieldsets = (
        (_('Transfer Details'), {
            'fields': ('player', 'from_club', 'to_club', 'request_date', 'status')
        }),
        (_('Financial'), {
            'fields': ('transfer_fee',)
        }),
        (_('Additional Information'), {
            'fields': ('reason', 'rejection_reason')
        }),
        (_('Approval Information'), {
            'fields': ('approved_by', 'approved_date', 'effective_date')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Only set approved_by on creation
            obj.approved_by = request.user.member_profile
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        # Only allow changes if transfer is pending
        return obj.status == 'PENDING'
