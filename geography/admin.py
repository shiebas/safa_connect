from django.contrib import admin
from .models import (
    RegistrationType, WorldSportsBody, Continent, ContinentFederation,
    ContinentRegion, Country, NationalFederation, Province, Region,
    Association, Club, CustomUser, Membership
)

admin.site.register(RegistrationType)
admin.site.register(WorldSportsBody)
admin.site.register(Continent)
admin.site.register(ContinentFederation)
admin.site.register(ContinentRegion)
admin.site.register(Country)
admin.site.register(NationalFederation)
admin.site.register(Province)
admin.site.register(Region)
admin.site.register(Association)
admin.site.register(Club)
admin.site.register(CustomUser)
admin.site.register(Membership)