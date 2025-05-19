# geography/urls.py
from django.urls import path
from . import views

app_name = 'geography'

urlpatterns = [
    # Home view
    path('', views.home, name='home'),
    
    # World Sports Bodies
    path('world-bodies/', views.world_bodies_list, name='world_bodies_list'),
    path('world-bodies/<int:pk>/', views.world_body_detail, name='world_body_detail'),
    
    # Continents
    path('continents/', views.continent_list, name='continent_list'),
    path('continents/<int:pk>/', views.continent_detail, name='continent_detail'),
    
    # Continental Federations
    path('continent-federations/', views.continent_federation_list, name='continent_federation_list'),
    path('continent-federations/<int:pk>/', views.continent_federation_detail, name='continent_federation_detail'),
    
    # Continental Regions
    path('continent-regions/', views.continent_region_list, name='continent_region_list'),
    path('continent-regions/<int:pk>/', views.continent_region_detail, name='continent_region_detail'),
    
    # Countries
    path('countries/', views.country_list, name='country_list'),
    path('countries/<int:pk>/', views.country_detail, name='country_detail'),
    
    # National Federations
    path('national-federations/', views.national_federation_list, name='national_federation_list'),
    path('national-federations/<int:pk>/', views.national_federation_detail, name='national_federation_detail'),
    
    # Provinces
    path('provinces/', views.province_list, name='province_list'),
    path('provinces/<int:pk>/', views.province_detail, name='province_detail'),
    
    # Regions
    path('regions/', views.region_list, name='region_list'),
    path('regions/<int:pk>/', views.region_detail, name='region_detail'),
    
    # Clubs
    path('clubs/', views.club_list, name='club_list'),
    path('clubs/<int:pk>/', views.club_detail, name='club_detail'),
    
    # Associations
    path('associations/', views.association_list, name='association_list'),
    path('associations/<int:pk>/', views.association_detail, name='association_detail'),
    
    # Registration & Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Member Profile
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Memberships
    path('memberships/', views.memberships, name='memberships'),
    path('memberships/new/', views.new_membership, name='new_membership'),
    path('memberships/<int:pk>/edit/', views.edit_membership, name='edit_membership'),
    
    # API endpoints for ajax filtering
    path('api/regions-by-province/<int:province_id>/', views.regions_by_province, name='regions_by_province'),
    path('api/clubs-by-region/<int:region_id>/', views.clubs_by_region, name='clubs_by_region'),
]
