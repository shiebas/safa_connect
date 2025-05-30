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

class LocalFootballAssociationAdmin(ModelWithLogoAdmin):
    list_display = ['name', 'acronym', 'region', 'display_logo']
    list_filter = ['region']
    search_fields = ['name', 'acronym']

class ClubAdmin(ModelWithLogoAdmin):
    list_display = ['name', 'short_name', 'region', 'local_football_association', 'display_logo']
    list_filter = ['region', 'local_football_association']
    search_fields = ['name', 'short_name']

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
