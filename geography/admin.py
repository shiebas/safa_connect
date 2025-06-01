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
    list_display = ['name', 'acronym', 'country', 'display_logo']
    list_filter = ['country']
    search_fields = ['name', 'acronym']

class ProvinceAdmin(ModelWithLogoAdmin):
    list_display = ['name', 'code', 'country', 'display_logo']
    list_filter = ['country']
    search_fields = ['name', 'code']

class AssociationAdmin(ModelWithLogoAdmin):
    list_display = ['name', 'acronym', 'national_federation', 'display_logo']
    list_filter = ['national_federation']
    search_fields = ['name', 'acronym']

class LocalFootballAssociationAdmin(admin.ModelAdmin):
    list_display = ['name', 'acronym', 'region', 'association', 'get_province']
    list_filter = ['region__province', 'region', 'association']
    search_fields = ['name', 'acronym', 'region__name']
    
    def get_province(self, obj):
        return obj.region.province.name
    get_province.short_description = 'Province'
    get_province.admin_order_field = 'region__province__name'

class ClubAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'code',
        'get_region',
        'get_lfa',
        'stadium',
        'founding_date'
    ]
    list_filter = [
        'localfootballassociation__region',  # Filter by region through the relationship
        'localfootballassociation'  # Filter by LFA
    ]
    search_fields = [
        'name',
        'code',
        'localfootballassociation__name',
        'localfootballassociation__region__name'
    ]
    
    # Define methods to get related fields for list_display
    def get_region(self, obj):
        return obj.localfootballassociation.region.name
    get_region.short_description = 'Region'
    get_region.admin_order_field = 'localfootballassociation__region__name'
    
    def get_lfa(self, obj):
        return obj.localfootballassociation.name
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
admin.site.register(Region)
admin.site.register(LocalFootballAssociation, LocalFootballAssociationAdmin)
admin.site.register(Association, AssociationAdmin)
admin.site.register(Club, ClubAdmin)
