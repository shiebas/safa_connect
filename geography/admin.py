from django.contrib import admin
from django import forms
from utils.admin import ModelWithLogoAdmin
from .models import (
    WorldSportsBody, Continent, ContinentFederation,
    ContinentRegion, Country, NationalFederation, Province, Region,
    Association, Club, LocalFootballAssociation
)
from django.utils.crypto import get_random_string
from django.contrib import messages

# Admin classes for models that inherit from ModelWithLogo
class ContinentFederationAdmin(ModelWithLogoAdmin):
    list_display = ['name', 'acronym', 'continent', 'world_body', 'display_logo']
    list_filter = ['continent', 'world_body']
    search_fields = ['name', 'acronym']

class ContinentRegionAdmin(ModelWithLogoAdmin):
    list_display = ['name', 'continent', 'description', 'logo']
    list_filter = ['continent']
    search_fields = ['name', 'code']

class CountryAdmin(ModelWithLogoAdmin):
    list_display = ['name', 'continent_region', 'display_logo']
    list_filter = ['continent_region']
    search_fields = ['name']


class NationalFederationAdmin(ModelWithLogoAdmin):
    list_display = ['name', 'acronym', 'country', 'safa_id', 'display_logo']
    list_filter = ['country']
    search_fields = ['name', 'acronym', 'safa_id']  # Added safa_id
    
class ProvinceAdmin(ModelWithLogoAdmin):
    list_display = ['name', 'get_region_count', 'display_logo']
    list_filter = []
    search_fields = ['name', 'code', 'safa_id']
    actions = ['generate_safa_ids']
    
    def generate_safa_ids(self, request, queryset):
        """Generate unique SAFA IDs for selected provinces"""
        import string
        import random
        
        updated_count = 0
        
        for province in queryset:
            if not province.safa_id:  # Only generate if empty
                while True:
                    # Generate 5-digit random alphanumeric SAFA ID (A-Z, 0-9)
                    chars = string.ascii_uppercase + string.digits
                    safa_id = ''.join(random.choices(chars, k=5))
                    
                    # Check if this ID already exists across the system
                    from .models import Province
                    if not Province.objects.filter(safa_id=safa_id).exists():
                        province.safa_id = safa_id
                        province.save(update_fields=['safa_id'])
                        updated_count += 1
                        break
        
        messages.success(request, f'Generated SAFA IDs for {updated_count} provinces.')
    
    generate_safa_ids.short_description = "Generate SAFA IDs for selected provinces"
    
    def get_region_count(self, obj):
        return obj.region_set.count()  # Changed from regions to region_set
    get_region_count.short_description = 'Number of Regions'

class AssociationAdmin(ModelWithLogoAdmin):
    list_display = ['name', 'acronym', 'national_federation', 'safa_id', 'display_logo']
    list_filter = ['national_federation']
    search_fields = ['name', 'acronym', 'safa_id']
    readonly_fields = ('safa_id',)  # Only include actual readonly fields
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'province']
    list_filter = ['province', 'created']
    search_fields = ['name', 'safa_id', 'province__name']
    list_per_page = 50  # Show 50 regions per page instead of default 25
    ordering = ['province__name', 'name']

class LocalFootballAssociationAdmin(admin.ModelAdmin):
    list_display = ['name', 'region']
    list_filter = ['region']
    search_fields = ['name', 'region__name']
    list_per_page = 50  # Show 50 LFAs per page instead of default 25
    ordering = ['region__province__name', 'region__name', 'name']
    
    def get_province(self, obj):
        return obj.region.province.name if obj.region and obj.region.province else '-'
    get_province.short_description = 'Province'
    get_province.admin_order_field = 'region__province__name'

class ClubAdmin(ModelWithLogoAdmin):
    list_display = ['name', 'localfootballassociation', 'status', 'display_logo']
    list_filter = ['localfootballassociation', 'status']
    search_fields = ['name', 'localfootballassociation__name', 'safa_id']
    list_editable = []
    
    def get_province(self, obj):
        return obj.localfootballassociation.region.province.name if obj.localfootballassociation else '-'
    get_province.short_description = 'Province'
    
    def get_region(self, obj):
        return obj.localfootballassociation.region.name if obj.localfootballassociation else '-'
    get_region.short_description = 'Region'
    
# Register models
admin.site.register(WorldSportsBody)
admin.site.register(Continent)
admin.site.register(ContinentFederation, ContinentFederationAdmin)
admin.site.register(ContinentRegion, ContinentRegionAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(NationalFederation, NationalFederationAdmin)
admin.site.register(Province, ProvinceAdmin)
admin.site.register(LocalFootballAssociation, LocalFootballAssociationAdmin)
admin.site.register(Association, AssociationAdmin)
admin.site.register(Club, ClubAdmin)
# Note: Region is registered using @admin.register decorator above, so no need to register it here

# Custom admin site configuration
admin.site.site_header = "SAFA Administration"
admin.site.site_title = "SAFA Admin Portal"
admin.site.index_title = "Welcome to SAFA Administration Portal"

class CustomAdminSite(admin.AdminSite):
    class Media:
        css = {
            'all': ('admin/custom_admin.css',)
        }

for model, modeladmin in admin.site._registry.items():
    modeladmin.Media = type('Media', (), {
        'css': {'all': ('admin/custom_admin.css',)}
    })
