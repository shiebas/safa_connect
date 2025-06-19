from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import (
    WorkingLoginView, working_home, register, 
    check_username, user_qr_code, profile_view, 
    model_debug_view,  # Remove generate_safa_id_ajax
    check_email_availability, check_id_number_availability,
    registration_portal, province_registration, club_registration,
    national_registration, lfa_registration,
    update_profile_photo, CustomUserViewSet, lfa_admin_approvals,
    dashboard, club_admin_add_player,
    api_regions, api_clubs, api_lfas,
    ajax_check_id_number, ajax_check_passport_number, ajax_check_sa_passport_number,
    player_approval_list, player_detail, approve_player, unapprove_player,
    edit_player, club_invoices, player_statistics
)
from .views_mcp import MCPUserListView
from .api_auth import APILoginView
from rest_framework import routers

app_name = 'accounts'

router = routers.DefaultRouter()
router.register(r'users', CustomUserViewSet)

urlpatterns = [
    # Regular views
    path('', working_home, name='home'),
    path('login/', WorkingLoginView.as_view(), name='login'),
    path('home/', working_home, name='working_home'),
    path('register/', register, name='register'),
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
    path('registration-portal/', registration_portal, name='registration_portal'),
    path('register/province/', province_registration, name='province_registration'),
    path('register/national/', national_registration, name='national_registration'),
    path('register/lfa/', lfa_registration, name='lfa_registration'),
    path('register/club/', club_registration, name='club_registration'),
    path('lfa-admin/approvals/', lfa_admin_approvals, name='lfa_admin_approvals'),
    path('dashboard/', dashboard, name='dashboard'),
    path('club-admin/add-player/', club_admin_add_player, name='club_admin_add_player'),
    path('players/approval-list/', player_approval_list, name='player_approval_list'),
    path('players/<int:player_id>/', player_detail, name='player_detail'),
    path('players/<int:player_id>/edit/', edit_player, name='edit_player'),
    path('players/<int:player_id>/approve/', approve_player, name='approve_player'),
    path('players/<int:player_id>/unapprove/', unapprove_player, name='unapprove_player'),
    path('club-admin/invoices/', club_invoices, name='club_invoices'),
    path('admin/player-statistics/', player_statistics, name='player_statistics'),
    # --- API endpoints below ---
    path('api/regions/', api_regions, name='api_regions'),
    path('api/clubs/', api_clubs, name='api_clubs'),
    path('api/lfas/', api_lfas, name='api_lfas'),
    path('api/mcp/users/', MCPUserListView.as_view(), name='mcp_user_list'),
    path('api/', include(router.urls)),
    path('api/login/', APILoginView.as_view(), name='api_login'),
    # Add other paths as needed
]
