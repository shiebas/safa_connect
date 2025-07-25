# registration/urls.py
from django.urls import path
from . import views

app_name = 'registration'

urlpatterns = [
    # Main registration endpoints
    path('', views.universal_registration, name='universal_registration'),
    path('success/', views.registration_success, name='registration_success'),
    
    # Approval dashboard
    path('approval-dashboard/', views.member_approval_dashboard, name='approval_dashboard'),
    path('approve-member/<int:member_id>/', views.approve_member, name='approve_member'),
    path('reject-member/<int:member_id>/', views.reject_member, name='reject_member'),
    path('member-details/<int:member_id>/', views.member_details, name='member_details'),
    
    # Bulk actions
    path('bulk-action/', views.bulk_member_action, name='bulk_member_action'),
    path('send-payment-reminder/<int:member_id>/', views.send_payment_reminder, name='send_payment_reminder'),
    
    # AJAX validation endpoints
    path('ajax/validate-id/', views.ajax_validate_id, name='ajax_validate_id'),
    path('ajax/validate-email/', views.ajax_validate_email, name='ajax_validate_email'),
    path('ajax/validate-safa-id/', views.ajax_validate_safa_id, name='ajax_validate_safa_id'),
    
    # Geography cascade APIs
    path('api/regions/', views.api_regions, name='api_regions'),
    path('api/lfas/', views.api_lfas, name='api_lfas'),
    path('api/clubs/', views.api_clubs, name='api_clubs'),
    
    # Export and reporting
    path('export-members/', views.export_members, name='export_members'),
    path('generate-report/', views.generate_report, name='generate_report'),
    
    # Legacy endpoints (for backward compatibility)
    path('senior/', views.senior_registration, name='senior_registration'),
    path('club-admin/add-player/', views.club_admin_add_player, name='club_admin_add_player'),
]