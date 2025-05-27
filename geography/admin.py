from django.contrib import admin
from django.utils.html import format_html
from .models import (
    RegistrationType, WorldSportsBody, Continent, ContinentFederation,
    ContinentRegion, Country, NationalFederation, Province, Region,
    Association, Club, CustomUser, Membership, LocalFootballAssociation
)

# Base admin class for models with logo
class ModelWithLogoAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'display_logo']

    def display_logo(self, obj):
        return format_html('<img src="{}" width="50" height="50" />', obj.logo_url)

    display_logo.short_description = 'Logo'

# Admin classes for models that inherit from ModelWithLogo
class ContinentFederationAdmin(ModelWithLogoAdmin):
    list_display = ['name', 'acronym', 'continent', 'world_body', 'display_logo']
    list_filter = ['continent', 'world_body']
    search_fields = ['name', 'acronym']

class ContinentRegionAdmin(ModelWithLogoAdmin):
    list_display = ['name', 'acronym', 'continent_federation', 'display_logo']
    list_filter = ['continent_federation']
    search_fields = ['name', 'acronym']

class CountryAdmin(ModelWithLogoAdmin):
    list_display = ['name', 'continent_region', 'display_logo']
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
admin.site.register(RegistrationType)
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
admin.site.register(CustomUser)
admin.site.register(Membership)
