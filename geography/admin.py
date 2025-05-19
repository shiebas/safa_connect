# geography/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    RegistrationType,
    WorldSportsBody,
    Continent,
    ContinentFederation,
    ContinentRegion,
    Country,
    NationalFederation,
    Province,
    Region,
    Association,
    Club,
    CustomUser,
    Membership
)

class TimeStampedModelAdmin(admin.ModelAdmin):
    """Base admin class for models with timestamps"""
    readonly_fields = ('created', 'modified')
    list_display = ('__str__', 'created', 'modified')

# Register the base models
@admin.register(RegistrationType)
class RegistrationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'allowed_user_roles')
    search_fields = ('name',)

# Register hierarchical models
@admin.register(WorldSportsBody)
class WorldSportsBodyAdmin(TimeStampedModelAdmin):
    list_display = ('acronym', 'name', 'sport_code')
    search_fields = ('name', 'acronym')
    list_filter = ('sport_code',)
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" />', obj.logo.url)
        return "No Logo"
    
    readonly_fields = ('logo_preview',) + TimeStampedModelAdmin.readonly_fields

@admin.register(Continent)
class ContinentAdmin(TimeStampedModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name',)
    list_filter = ('code',)

@admin.register(ContinentFederation)
class ContinentFederationAdmin(TimeStampedModelAdmin):
    list_display = ('acronym', 'name', 'continent', 'world_body')
    search_fields = ('name', 'acronym')
    list_filter = ('continent', 'world_body')

@admin.register(ContinentRegion)
class ContinentRegionAdmin(TimeStampedModelAdmin):
    list_display = ('acronym', 'name', 'continent_federation')
    search_fields = ('name', 'acronym')
    list_filter = ('continent_federation',)

@admin.register(Country)
class CountryAdmin(TimeStampedModelAdmin):
    list_display = ('name', 'fifa_code', 'association_acronym', 'is_default')
    search_fields = ('name', 'fifa_code')
    list_filter = ('continent_region', 'is_default')

@admin.register(NationalFederation)
class NationalFederationAdmin(TimeStampedModelAdmin):
    list_display = ('acronym', 'name', 'country', 'world_body')
    search_fields = ('name', 'acronym')
    list_filter = ('country', 'world_body')

@admin.register(Province)
class ProvinceAdmin(TimeStampedModelAdmin):
    list_display = ('name', 'code', 'country')
    search_fields = ('name', 'code')
    list_filter = ('country',)

@admin.register(Region)
class RegionAdmin(TimeStampedModelAdmin):
    list_display = ('name', 'code', 'province', 'national_federation')
    search_fields = ('name', 'code')
    list_filter = ('province', 'national_federation')

@admin.register(Association)
class AssociationAdmin(TimeStampedModelAdmin):
    list_display = ('acronym', 'name', 'association_type', 'national_federation')
    search_fields = ('name', 'acronym')
    list_filter = ('association_type', 'national_federation')

@admin.register(Club)
class ClubAdmin(TimeStampedModelAdmin):
    list_display = ('name', 'short_name', 'region', 'founded_year')
    search_fields = ('name', 'short_name')
    list_filter = ('region', 'region__province')
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" />', obj.logo.url)
        return "No Logo"
    
    readonly_fields = ('logo_preview',) + TimeStampedModelAdmin.readonly_fields

# Custom user related admin
class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1
    fields = ('membership_type', 'club', 'association', 'national_federation', 
              'start_date', 'end_date', 'is_active', 'player_category')

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'name', 'surname', 'role', 'country')
    search_fields = ('username', 'email', 'name', 'surname')
    list_filter = ('role', 'country', 'registration_type')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('name', 'middle_name', 'surname', 'alias', 'email', 
                                     'date_of_birth', 'gender', 'country')}),
        ('Identification', {'fields': ('id_document_type', 'id_number', 'id_number_other', 
                                      'passport_number')}),
        ('Profile', {'fields': ('profile_photo', 'role', 'registration_type')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'registration_date')}),
    )
    inlines = [MembershipInline]

@admin.register(Membership)
class MembershipAdmin(TimeStampedModelAdmin):
    list_display = ('user', 'membership_type', 'get_organization', 'start_date', 'end_date', 'is_active')
    search_fields = ('user__username', 'user__name', 'user__surname')
    list_filter = ('membership_type', 'is_active', 'player_category')
    
    def get_organization(self, obj):
        if obj.club:
            return f"Club: {obj.club.name}"
        elif obj.association:
            return f"Association: {obj.association.name}"
        elif obj.national_federation:
            return f"Federation: {obj.national_federation.name}"
        return "Unknown"
    
    get_organization.short_description = 'Organization'
