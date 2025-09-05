from django.urls import path
from . import views

app_name = 'tournament_verification'

urlpatterns = [
    # Public URLs
    path('', views.tournament_list, name='tournament_list'),
    path('teams/<uuid:tournament_id>/', views.team_selection, name='team_selection'),
    path('teams-list/<uuid:tournament_id>/', views.team_list, name='team_list'),
    path('fixtures/<uuid:tournament_id>/', views.tournament_fixtures, name='tournament_fixtures'),
    path('register/<uuid:tournament_id>/<uuid:team_id>/', views.tournament_registration, name='tournament_registration'),
    path('success/<uuid:registration_id>/', views.registration_success, name='registration_success'),
    
    # Admin URLs (require login)
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/verify/', views.photo_verification, name='photo_verification'),
    path('verify/<uuid:registration_id>/', views.verify_registration, name='verify_registration'),
    path('auto-verify/<uuid:registration_id>/', views.auto_verify_registration, name='auto_verify_registration'),
    path('upload-reference/<uuid:registration_id>/', views.upload_reference_photo, name='upload_reference_photo'),
    path('generate-team-photo/<uuid:team_id>/', views.generate_team_photo, name='generate_team_photo'),
    path('generate-fixtures/<uuid:tournament_id>/', views.generate_fixtures, name='generate_fixtures'),
    path('bulk-delete/registrations/', views.bulk_delete_registrations, name='bulk_delete_registrations'),
    path('bulk-delete/teams/', views.bulk_delete_teams, name='bulk_delete_teams'),
    path('bulk-delete/tournaments/', views.bulk_delete_tournaments, name='bulk_delete_tournaments'),
    path('bulk-management/', views.bulk_management, name='bulk_management'),
    path('dashboard/<uuid:tournament_id>/', views.tournament_dashboard, name='tournament_dashboard'),
    path('manual-verify/<uuid:registration_id>/', views.manual_verification, name='manual_verification'),
]
