from django.urls import path, include
from rest_framework import routers
from . import views
from .views import (
    WorldSportsBodyViewSet, ContinentViewSet, ContinentFederationViewSet, ContinentRegionViewSet, CountryViewSet, NationalFederationViewSet, ProvinceViewSet, RegionViewSet, AssociationViewSet, LocalFootballAssociationViewSet, ClubViewSet
)

app_name = 'geography'  # This should be defined only once

router = routers.DefaultRouter()
router.register(r'worldsportsbodies', WorldSportsBodyViewSet)
router.register(r'continents', ContinentViewSet)
router.register(r'continentfederations', ContinentFederationViewSet)
router.register(r'continentregions', ContinentRegionViewSet)
router.register(r'countries', CountryViewSet)
router.register(r'nationalfederations', NationalFederationViewSet)
router.register(r'provinces', ProvinceViewSet)
router.register(r'regions', RegionViewSet)
router.register(r'associations', AssociationViewSet)
router.register(r'localfootballassociations', LocalFootballAssociationViewSet)
router.register(r'clubs', ClubViewSet)

urlpatterns = [
    path('admin/', views.geography_admin, name='geography_admin'),
    path('advanced/', views.advanced_home, name='advance_home'),
    # Geography home and optimized list views (main navigation)
    path('', views.geography_home, name='geography-home'),
    path('provinces/', views.province_list_view, name='provinces'),
    path('regions/', views.region_list_view, name='regions'),
    path('lfas/', views.lfa_list_view, name='lfas'),
    path('clubs/', views.club_list_view, name='clubs'),  # Now uses the clean function-based view
    # Better LFA views
    path('lfas/hierarchical/', views.lfa_hierarchical_view, name='lfa_hierarchical'),
    # Debug URLs
    path('debug/province-regions/', views.debug_province_regions, name='debug_province_regions'),
    path('debug/fix-duplicate-regions/', views.fix_duplicate_regions, name='fix_duplicate_regions'),
    # Detail views
    path('provinces/<int:pk>/', views.province_detail, name='province-detail'),
    path('regions/<int:pk>/', views.region_detail, name='region-detail'),
    path('lfas/<int:pk>/', views.lfa_detail, name='lfa-detail'),
    # Add back the hierarchical navigation URLs that templates expect
    path('provinces/<int:province_id>/regions/', views.province_regions, name='province_regions'),
    path('regions/<int:region_id>/lfas/', views.region_lfas, name='region_lfas'),
    path('lfas/<int:lfa_id>/clubs/', views.lfa_clubs, name='lfa_clubs'),
    # WorldSportsBody
    path('worldsportsbodies/', views.WorldSportsBodyListView.as_view(), name='worldsportsbody-list'),
    path('worldsportsbodies/add/', views.WorldSportsBodyCreateView.as_view(), name='worldsportsbody-create'),
    path('worldsportsbodies/<int:pk>/', views.WorldSportsBodyDetailView.as_view(), name='worldsportsbody-detail'),
    path('worldsportsbodies/<int:pk>/edit/', views.WorldSportsBodyUpdateView.as_view(), name='worldsportsbody-update'),
    path('worldsportsbodies/<int:pk>/delete/', views.WorldSportsBodyDeleteView.as_view(), name='worldsportsbody-delete'),
    # Continent
    path('continents/', views.ContinentListView.as_view(), name='continent-list'),
    path('continents/add/', views.ContinentCreateView.as_view(), name='continent-create'),
    path('continents/<int:pk>/', views.ContinentDetailView.as_view(), name='continent-detail'),
    path('continents/<int:pk>/edit/', views.ContinentUpdateView.as_view(), name='continent-update'),
    path('continents/<int:pk>/delete/', views.ContinentDeleteView.as_view(), name='continent-delete'),
    # ContinentFederation
    path('continentfederations/', views.ContinentFederationListView.as_view(), name='continentfederation-list'),
    path('continentfederations/add/', views.ContinentFederationCreateView.as_view(), name='continentfederation-create'),
    path('continentfederations/<int:pk>/', views.ContinentFederationDetailView.as_view(), name='continentfederation-detail'),
    path('continentfederations/<int:pk>/edit/', views.ContinentFederationUpdateView.as_view(), name='continentfederation-update'),
    path('continentfederations/<int:pk>/delete/', views.ContinentFederationDeleteView.as_view(), name='continentfederation-delete'),
    # ContinentRegion
    path('continentregions/', views.ContinentRegionListView.as_view(), name='continentregion-list'),
    path('continentregions/add/', views.ContinentRegionCreateView.as_view(), name='continentregion-create'),
    path('continentregions/<int:pk>/', views.ContinentRegionDetailView.as_view(), name='continentregion-detail'),
    path('continentregions/<int:pk>/edit/', views.ContinentRegionUpdateView.as_view(), name='continentregion-update'),
    path('continentregions/<int:pk>/delete/', views.ContinentRegionDeleteView.as_view(), name='continentregion-delete'),
    # Country
    path('countries/', views.CountryListView.as_view(), name='country-list'),
    path('countries/add/', views.CountryCreateView.as_view(), name='country-create'),
    path('countries/<int:pk>/', views.CountryDetailView.as_view(), name='country-detail'),
    path('countries/<int:pk>/edit/', views.CountryUpdateView.as_view(), name='country-update'),
    path('countries/<int:pk>/delete/', views.CountryDeleteView.as_view(), name='country-delete'),
    # NationalFederation
    path('nationalfederations/', views.NationalFederationListView.as_view(), name='nationalfederation-list'),
    path('nationalfederations/add/', views.NationalFederationCreateView.as_view(), name='nationalfederation-create'),
    path('nationalfederations/<int:pk>/', views.NationalFederationDetailView.as_view(), name='nationalfederation-detail'),
    path('nationalfederations/<int:pk>/edit/', views.NationalFederationUpdateView.as_view(), name='nationalfederation-update'),
    path('nationalfederations/<int:pk>/delete/', views.NationalFederationDeleteView.as_view(), name='nationalfederation-delete'),
    # Association
    path('associations/', views.AssociationListView.as_view(), name='association-list'),
    path('associations/add/', views.AssociationCreateView.as_view(), name='association-create'),
    path('associations/<int:pk>/', views.AssociationDetailView.as_view(), name='association-detail'),
    path('associations/<int:pk>/edit/', views.AssociationUpdateView.as_view(), name='association-update'),
    path('associations/<int:pk>/delete/', views.AssociationDeleteView.as_view(), name='association-delete'),
    # Province
    path('provinces/', views.ProvinceListView.as_view(), name='province-list'),
    path('provinces/add/', views.ProvinceCreateView.as_view(), name='province-create'),
    path('provinces/<int:pk>/', views.ProvinceDetailView.as_view(), name='province-detail'),
    path('provinces/<int:pk>/edit/', views.ProvinceUpdateView.as_view(), name='province-update'),
    path('provinces/<int:pk>/delete/', views.ProvinceDeleteView.as_view(), name='province-delete'),
    # Region
    path('regions/', views.RegionListView.as_view(), name='region-list'),
    path('regions/add/', views.RegionCreateView.as_view(), name='region-create'),
    path('regions/<int:pk>/', views.RegionDetailView.as_view(), name='region-detail'),
    path('regions/<int:pk>/edit/', views.RegionUpdateView.as_view(), name='region-update'),
    path('regions/<int:pk>/delete/', views.RegionDeleteView.as_view(), name='region-delete'),
    # Club
    path('clubs/', views.ClubListView.as_view(), name='club-list'),
    path('clubs/add/', views.ClubCreateView.as_view(), name='club-create'),
    path('clubs/<int:pk>/', views.ClubDetailView.as_view(), name='club-detail'),
    path('clubs/<int:pk>/edit/', views.ClubUpdateView.as_view(), name='club-update'),
    path('clubs/<int:pk>/delete/', views.ClubDeleteView.as_view(), name='club-delete'),
    # LocalFootballAssociation
    path('localfootballassociations/', views.LocalFootballAssociationListView.as_view(), name='localfootballassociation-list'),
    path('localfootballassociations/add/', views.LocalFootballAssociationCreateView.as_view(), name='localfootballassociation-create'),
    path('localfootballassociations/<int:pk>/', views.LocalFootballAssociationDetailView.as_view(), name='localfootballassociation-detail'),
    path('localfootballassociations/<int:pk>/edit/', views.LocalFootballAssociationUpdateView.as_view(), name='localfootballassociation-update'),
    path('localfootballassociations/<int:pk>/delete/', views.LocalFootballAssociationDeleteView.as_view(), name='localfootballassociation-delete'),
    # Better LFA views
    path('lfas/hierarchical/', views.lfa_hierarchical_view, name='lfa_hierarchical'),
    # API URLs (non-router, if needed)
    path('api/regions/', views.api_regions, name='api_regions'),
    path('api/lfas/', views.api_lfas, name='api_lfas'),
    # DRF router: all API endpoints are only available under /api/
    # path('api/', include(router.urls)),
    path('clubs/register/', views.register_club, name='register-club'),
    path('club/compliance/', views.club_compliance_update, name='club_compliance_update'),
    path('lfa/info/', views.lfa_info_update, name='lfa_info_update'),
]
