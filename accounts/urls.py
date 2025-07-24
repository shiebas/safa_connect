from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from .views import (
    WorkingLoginView, working_home, 
    check_username, user_qr_code, profile_view, 
    model_debug_view, 
    check_email_availability, check_id_number_availability,
    registration_portal, 
    update_profile_photo, CustomUserViewSet, lfa_admin_approvals,
    dashboard, club_admin_add_official, association_admin_add_official,
    api_regions, api_clubs, api_lfas, api_associations_by_lfa,
    ajax_check_id_number, ajax_check_passport_number, ajax_check_sa_passport_number,
    ajax_check_safa_id, ajax_check_fifa_id, 
    player_approval_list, player_detail, approve_player, unapprove_player,
    edit_player, club_invoices, player_statistics, official_list,
    official_detail, add_official_certification, approve_official, unapprove_official, manage_official_associations, edit_official,
    invoice_detail_view,
    admin_registration_view
)
from .document_views import document_access_dashboard, document_access_report, document_access_api, protected_document_view
from .views_mcp import MCPUserListView
from .api_auth import APILoginView
from .views_admin_referees import admin_add_referee
from rest_framework import routers

# Simple test view function
def test_document_download(request):
    """Simple test view for document protection system"""
    html_content = """
    <html>
    <head><title>Test Document Protection</title></head>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>SAFA Document Protection System Test</h2>
        <p>Click the link below to test document download protection:</p>
        <p><a href="/media/test_document.txt" style="background: #006633; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Download Test Document</a></p>
        <p><small>This will trigger the document protection middleware and log the access.</small></p>
        <hr>
        <p><a href="/accounts/dashboard/">← Back to Dashboard</a></p>
    </body>
    </html>
    """
    return HttpResponse(html_content)

app_name = 'accounts'

router = routers.DefaultRouter()
router.register(r'users', CustomUserViewSet)

urlpatterns = [
    # Regular views
    path('', working_home, name='home'),
    path('login/', WorkingLoginView.as_view(), name='login'),
    path('home/', working_home, name='working_home'),
    path('register/', admin_registration_view, {'role_type': 'universal'}, name='register'),
    path('check-username/', check_username, name='check_username'),
    path('qr-code/', user_qr_code, name='qr_code'),
    path('profile/', profile_view, name='profile'),
    path('profile/update-photo/', update_profile_photo, name='update_profile_photo'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('ajax/check-email/', check_email_availability, name='check_email'),
    path('ajax/check-id-number/', check_id_number_availability, name='check_id_number'),
    path('ajax/check-id-number/', ajax_check_id_number, name='ajax_check_id_number'),
    path('ajax/check-passport-number/', ajax_check_passport_number, name='ajax_check_passport_number'),
    path('ajax/check-sa-passport-number/', ajax_check_sa_passport_number, name='ajax_check_sa_passport_number'),
    path('ajax/check-safa-id/', ajax_check_safa_id, name='ajax_check_safa_id'),
    path('ajax/check-fifa-id/', ajax_check_fifa_id, name='ajax_check_fifa_id'),
    path('registration-portal/', registration_portal, name='registration_portal'),
    path('register/province/', admin_registration_view, {'role_type': 'province'}, name='province_registration'),
    path('register/national/', admin_registration_view, {'role_type': 'national'}, name='national_registration'),
    path('register/lfa/', admin_registration_view, {'role_type': 'lfa'}, name='lfa_registration'),
    path('register/club/', admin_registration_view, {'role_type': 'club'}, name='club_registration'),
    path('register/association/', admin_registration_view, {'role_type': 'association'}, name='association_registration'),
    path('lfa-admin/approvals/', lfa_admin_approvals, name='lfa_admin_approvals'),
    path('dashboard/', dashboard, name='dashboard'),
    path('club-admin/add-official/', club_admin_add_official, name='club_admin_add_official'),
    path('association-admin/add-official/', association_admin_add_official, name='association_admin_add_official'),
    path('officials/', official_list, name='official_list'),
    path('players/approval-list/', player_approval_list, name='player_approval_list'),
    path('players/<str:safa_id>/', player_detail, name='player_detail'),
    path('players/<str:safa_id>/edit/', edit_player, name='edit_player'),
    path('players/<str:safa_id>/approve/', approve_player, name='approve_player'),
    path('players/<str:safa_id>/unapprove/', unapprove_player, name='unapprove_player'),
    path('club-admin/invoices/', club_invoices, name='club_invoices'),
    path('admin/player-statistics/', player_statistics, name='player_statistics'),
    # Official management URLs
    path('officials/<int:official_id>/', official_detail, name='official_detail'),
    path('officials/<int:official_id>/add-certification/', add_official_certification, name='add_official_certification'),
    path('officials/<int:official_id>/approve/', approve_official, name='approve_official'),
    path('officials/<int:official_id>/unapprove/', unapprove_official, name='unapprove_official'),
    path('officials/<int:official_id>/manage-associations/', manage_official_associations, name='manage_official_associations'),
    path('officials/<int:official_id>/edit/', edit_official, name='edit_official'),
    path('invoices/<int:invoice_id>/', invoice_detail_view, name='invoice_detail'),
    path('admin/add-referee/', admin_add_referee, name='admin_add_referee'),
    
    # Document Protection & Access Tracking
    path('document-access/dashboard/', document_access_dashboard, name='document_access_dashboard'),
    path('document-access/api/', document_access_api, name='document_access_api'),
    path('document-access/report/', document_access_report, name='document_access_report'),
    path('protected-document/<str:document_id>/', protected_document_view, name='protected_document'),
    path('test-download/', test_document_download, name='test_download'),
    
    # --- API endpoints below ---
    path('api/regions/', api_regions, name='api_regions'),
    path('api/clubs/', api_clubs, name='api_clubs'),
    path('api/lfas/', api_lfas, name='api_lfas'),
    path('api/mcp/users/', MCPUserListView.as_view(), name='mcp_user_list'),
    path('api/', include(router.urls)),
    path('api/login/', APILoginView.as_view(), name='api_login'),
]