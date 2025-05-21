from django.urls import path
from . import views
from .views import geography_admin,WorldSportsBodyListView, WorldSportsBodyDetailView,
    WorldSportsBodyCreateView, WorldSportsBodyUpdateView,
    WorldSportsBodyDeleteView

app_name = 'geography'

urlpatterns = [
    path('admin/', geography_admin, name='geography_admin'),
    
    # Country
    path('countries/', views.CountryListView.as_view(), name='country-list'),
    path('countries/<int:pk>/', views.CountryDetailView.as_view(), name='country-detail'),

    # Province
    path('provinces/', views.ProvinceListView.as_view(), name='province-list'),
    path('provinces/<int:pk>/', views.ProvinceDetailView.as_view(), name='province-detail'),

    # Region
    path('regions/', views.RegionListView.as_view(), name='region-list'),
    path('regions/<int:pk>/', views.RegionDetailView.as_view(), name='region-detail'),

    # WorldSportsBody
    path('worldsportsbodies/', WorldSportsBodyListView.as_view(), name='worldsportsbody-list'),
    path('worldsportsbodies/add/', WorldSportsBodyCreateView.as_view(), name='worldsportsbody-create'),
    path('worldsportsbodies/<int:pk>/', WorldSportsBodyDetailView.as_view(), name='worldsportsbody-detail'),
    path('worldsportsbodies/<int:pk>/edit/', WorldSportsBodyUpdateView.as_view(), name='worldsportsbody-update'),
    path('worldsportsbodies/<int:pk>/delete/', WorldSportsBodyDeleteView.as_view(), name='worldsportsbody-delete'),
]
    # Continent
    path('continents/', views.ContinentListView.as_view(), name='continent-list'),
    path('continents/<int:pk>/', views.ContinentDetailView.as_view(), name='continent-detail'),

    # ContinentFederation
    path('continent-federations/', views.ContinentFederationListView.as_view(), name='continentfederation-list'),
    path('continent-federations/<int:pk>/', views.ContinentFederationDetailView.as_view(), name='continentfederation-detail'),

    # Club
    path('clubs/', views.ClubListView.as_view(), name='club-list'),
    path('clubs/<int:pk>/', views.ClubDetailView.as_view(), name='club-detail'),

    # Association
    path('associations/', views.AssociationListView.as_view(), name='association-list'),
    path('associations/<int:pk>/', views.AssociationDetailView.as_view(), name='association-detail'),

    # Membership
    path('memberships/', views.MembershipListView.as_view(), name='membership-list'),
    path('memberships/<int:pk>/', views.MembershipDetailView.as_view(), name='membership-detail'),
]
