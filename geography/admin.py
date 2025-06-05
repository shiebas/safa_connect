from django.contrib import admin
from utils.admin import ModelWithLogoAdmin
from .models import (
    WorldSportsBody, Continent, ContinentFederation,
    ContinentRegion, Country, NationalFederation, Province, Region,
    Association, Club, LocalFootballAssociation
)

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
    # Fix: 'country' isn't a field - use 'continent_region' instead
    list_filter = ['continent_region']
    search_fields = ['name']


class NationalFederationAdmin(ModelWithLogoAdmin):
    list_display = ['name', 'acronym', 'country', 'safa_id', 'display_logo']  # Added safa_id
    list_filter = ['country']
    search_fields = ['name', 'acronym', 'safa_id']  # Added safa_id

class ProvinceAdmin(ModelWithLogoAdmin):
    list_display = ['name', 'code', 'country', 'display_logo']
    list_filter = ['country']
    search_fields = ['name', 'code']

class AssociationAdmin(ModelWithLogoAdmin):
    list_display = ['name', 'acronym', 'national_federation', 'safa_id', 'display_logo']  # Added safa_id
    list_filter = ['national_federation']
    search_fields = ['name', 'acronym', 'safa_id']  # Added safa_id

class RegionAdmin(ModelWithLogoAdmin):  # Added RegionAdmin
    list_display = ['name', 'province', 'safa_id', 'display_logo']  # Removed 'association'
    list_filter = ['province']  # Removed 'association'
    search_fields = ['name', 'safa_id', 'province__name']

class LocalFootballAssociationAdmin(ModelWithLogoAdmin):  # Changed to ModelWithLogoAdmin
    list_display = ['name', 'acronym', 'region', 'association', 'safa_id', 'get_province', 'display_logo']  # Added safa_id and display_logo
    list_filter = ['region__province', 'region', 'association']
    search_fields = ['name', 'acronym', 'region__name', 'safa_id']  # Added safa_id
    
    def get_province(self, obj):
        return obj.region.province.name
    get_province.short_description = 'Province'
    get_province.admin_order_field = 'region__province__name'

class ClubAdmin(ModelWithLogoAdmin):
    list_display = [
        'name',
        'code',
        'safa_id',
        'status',
        'get_lfa',
        'get_region',
        'get_province',
        'stadium',
        'founding_date',
        'display_logo'
    ]
    list_filter = [
        'status',
        'localfootballassociation__region__province',
        'localfootballassociation__region',
        'localfootballassociation',
    ]
    search_fields = [
        'name',
        'code',
        'safa_id',
        'localfootballassociation__name',
        'localfootballassociation__region__name',
        'localfootballassociation__region__province__name',
    ]
    
    def get_region(self, obj):
        return obj.region.name if obj.region else '-'
    get_region.short_description = 'Region'
    get_region.admin_order_field = 'localfootballassociation__region__name'
    
    def get_province(self, obj):
        return obj.province.name if obj.province else '-'
    get_province.short_description = 'Province'
    get_province.admin_order_field = 'localfootballassociation__region__province__name'
    
    def get_lfa(self, obj):
        return obj.localfootballassociation.name if obj.localfootballassociation else '-'
    get_lfa.short_description = 'Local Football Association'
    get_lfa.admin_order_field = 'localfootballassociation__name'

# Register models
admin.site.register(WorldSportsBody)
admin.site.register(Continent)
admin.site.register(ContinentFederation, ContinentFederationAdmin)
admin.site.register(ContinentRegion, ContinentRegionAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(NationalFederation, NationalFederationAdmin)
admin.site.register(Province, ProvinceAdmin)
admin.site.register(Region, RegionAdmin)  # Added RegionAdmin
admin.site.register(LocalFootballAssociation, LocalFootballAssociationAdmin)
admin.site.register(Association, AssociationAdmin)
admin.site.register(Club, ClubAdmin)

admin.site.site_header = "Your Admin"
admin.site.site_title = "Your Admin Portal"
admin.site.index_title = "Welcome to Your Admin"

class CustomAdminSite(admin.AdminSite):
    class Media:
        css = {
            'all': ('admin/custom_admin.css',)
        }

# Or, for all ModelAdmins:
for model, modeladmin in admin.site._registry.items():
    modeladmin.Media = type('Media', (), {
        'css': {'all': ('admin/custom_admin.css',)}
    })
