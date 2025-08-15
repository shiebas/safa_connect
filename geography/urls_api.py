from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    WorldSportsBodyViewSet, ContinentViewSet, ContinentFederationViewSet,
    ContinentRegionViewSet, CountryViewSet, NationalFederationViewSet,
    ProvinceViewSet, RegionViewSet, AssociationViewSet,
    LocalFootballAssociationViewSet, ClubViewSet, get_organizations,
)

router = DefaultRouter()
router.register(r'worldsportsbodies', WorldSportsBodyViewSet)
router.register(r'continents', ContinentViewSet)
router.register(r'continentfederations', ContinentFederationViewSet)
router.register(r'continentregions', ContinentRegionViewSet)
router.register(r'countries', CountryViewSet)
router.register(r'nationalfederations', NationalFederationViewSet)
router.register(r'provinces', ProvinceViewSet)
router.register(r'regions', RegionViewSet)
router.register(r'associations', AssociationViewSet)
router.register(r'lfas', LocalFootballAssociationViewSet)
router.register(r'clubs', ClubViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('<str:org_type>/', get_organizations, name='get_organizations'),
]
