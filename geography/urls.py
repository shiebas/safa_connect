from django.urls import path
from . import views
from .views import (
    geography_admin, WorldSportsBodyListView, WorldSportsBodyDetailView,
    WorldSportsBodyCreateView, WorldSportsBodyUpdateView, WorldSportsBodyDeleteView, 
    ContinentListView, ContinentCreateView, ContinentDetailView, ContinentUpdateView, 
    ContinentDeleteView, ContinentFederationListView, ContinentFederationDetailView,
    ContinentFederationCreateView, ContinentFederationUpdateView, ContinentFederationDeleteView, 
    ContinentRegionListView, ContinentRegionCreateView, ContinentRegionDetailView,
    ContinentRegionUpdateView, ContinentRegionDeleteView, CountryListView, CountryCreateView, 
    CountryDetailView, CountryUpdateView, CountryDeleteView, NationalFederationListView, 
    NationalFederationCreateView, NationalFederationDetailView, NationalFederationUpdateView,
    NationalFederationDeleteView, AssociationListView, AssociationCreateView, 
    AssociationDetailView, AssociationUpdateView, AssociationDeleteView, ProvinceListView, 
    ProvinceCreateView, ProvinceDetailView, ProvinceUpdateView, ProvinceDeleteView, 
    RegionListView, RegionCreateView, RegionDetailView, RegionUpdateView, RegionDeleteView, 
    ClubListView, ClubCreateView, ClubDetailView, ClubUpdateView, ClubDeleteView,
    MembershipListView, MembershipCreateView, MembershipDetailView, MembershipUpdateView, 
    MembershipDeleteView
                     
)

app_name = 'geography'

urlpatterns = [

    path('admin/', geography_admin, name='geography_admin'),
    
    # WorldSportsBody
    path('worldsportsbodies/', WorldSportsBodyListView.as_view(), name='worldsportsbody-list'),
    path('worldsportsbodies/add/', WorldSportsBodyCreateView.as_view(), name='worldsportsbody-create'),
    path('worldsportsbodies/<int:pk>/', WorldSportsBodyDetailView.as_view(), name='worldsportsbody-detail'),
    path('worldsportsbodies/<int:pk>/edit/', WorldSportsBodyUpdateView.as_view(), name='worldsportsbody-update'),
    path('worldsportsbodies/<int:pk>/delete/', WorldSportsBodyDeleteView.as_view(), name='worldsportsbody-delete'),

    # Continent
    path('continents/', ContinentListView.as_view(), name='continent-list'),
    path('continents/add/', ContinentCreateView.as_view(), name='continent-create'),
    path('continents/<int:pk>/', ContinentDetailView.as_view(), name='continent-detail'),
    path('continents/<int:pk>/edit/', ContinentUpdateView.as_view(), name='continent-update'),
    path('continents/<int:pk>/delete/', ContinentDeleteView.as_view(), name='continent-delete'),

    # ContinentFederation
    path('continentfederations/', ContinentFederationListView.as_view(), name='continentfederation-list'),
    path('continentfederations/add/', ContinentFederationCreateView.as_view(), name='continentfederation-create'),
    path('continentfederations/<int:pk>/', ContinentFederationDetailView.as_view(), name='continentfederation-detail'),
    path('continentfederations/<int:pk>/edit/', ContinentFederationUpdateView.as_view(), name='continentfederation-update'),
    path('continentfederations/<int:pk>/delete/', ContinentFederationDeleteView.as_view(), name='continentfederation-delete'),

    # ContinentRegion
    path('continentregions/', ContinentRegionListView.as_view(), name='continentregion-list'),
    path('continentregions/add/', ContinentRegionCreateView.as_view(), name='continentregion-create'),
    path('continentregions/<int:pk>/', ContinentRegionDetailView.as_view(), name='continentregion-detail'),
    path('continentregions/<int:pk>/edit/', ContinentRegionUpdateView.as_view(), name='continentregion-update'),
    path('continentregions/<int:pk>/delete/', ContinentRegionDeleteView.as_view(), name='continentregion-delete'),

    # Country
    path('countries/', CountryListView.as_view(), name='country-list'),
    path('countries/add/', CountryCreateView.as_view(), name='country-create'),
    path('countries/<int:pk>/', CountryDetailView.as_view(), name='country-detail'),
    path('countries/<int:pk>/edit/', CountryUpdateView.as_view(), name='country-update'),
    path('countries/<int:pk>/delete/', CountryDeleteView.as_view(), name='country-delete'),

    # NationalFederation
    path('nationalfederations/', NationalFederationListView.as_view(), name='nationalfederation-list'),
    path('nationalfederations/add/', NationalFederationCreateView.as_view(), name='nationalfederation-create'),
    path('nationalfederations/<int:pk>/', NationalFederationDetailView.as_view(), name='nationalfederation-detail'),
    path('nationalfederations/<int:pk>/edit/', NationalFederationUpdateView.as_view(), name='nationalfederation-update'),
    path('nationalfederations/<int:pk>/delete/', NationalFederationDeleteView.as_view(), name='nationalfederation-delete'),

    # Association
    path('associations/', AssociationListView.as_view(), name='association-list'),
    path('associations/add/', AssociationCreateView.as_view(), name='association-create'),
    path('associations/<int:pk>/', AssociationDetailView.as_view(), name='association-detail'),
    path('associations/<int:pk>/edit/', AssociationUpdateView.as_view(), name='association-update'),
    path('associations/<int:pk>/delete/', AssociationDeleteView.as_view(), name='association-delete'),
    
    # Province
    path('provinces/', ProvinceListView.as_view(), name='province-list'),
    path('provinces/add/', ProvinceCreateView.as_view(), name='province-create'),
    path('provinces/<int:pk>/', ProvinceDetailView.as_view(), name='province-detail'),
    path('provinces/<int:pk>/edit/', ProvinceUpdateView.as_view(), name='province-update'),
    path('provinces/<int:pk>/delete/', ProvinceDeleteView.as_view(), name='province-delete'),

    # Region
    path('regions/', RegionListView.as_view(), name='region-list'),
    path('regions/add/', RegionCreateView.as_view(), name='region-create'),
    path('regions/<int:pk>/', RegionDetailView.as_view(), name='region-detail'),
    path('regions/<int:pk>/edit/', RegionUpdateView.as_view(), name='region-update'),
    path('regions/<int:pk>/delete/', RegionDeleteView.as_view(), name='region-delete'),

    # Club
    path('clubs/', ClubListView.as_view(), name='club-list'),
    path('clubs/add/', ClubCreateView.as_view(), name='club-create'),
    path('clubs/<int:pk>/', ClubDetailView.as_view(), name='club-detail'),
    path('clubs/<int:pk>/edit/', ClubUpdateView.as_view(), name='club-update'),
    path('clubs/<int:pk>/delete/', ClubDeleteView.as_view(), name='club-delete'),

    # Membership
    path('memberships/', MembershipListView.as_view(), name='membership-list'),
    path('memberships/add/', MembershipCreateView.as_view(), name='membership-create'),
    path('memberships/<int:pk>/', MembershipDetailView.as_view(), name='membership-detail'),
    path('memberships/<int:pk>/edit/', MembershipUpdateView.as_view(), name='membership-update'),
    path('memberships/<int:pk>/delete/', MembershipDeleteView.as_view(), name='membership-delete'),

]
