# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, views_admin_referees
from .views import (
    modern_home, profile, edit_profile, generate_digital_card
)

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('registration/', views.user_registration, name='user_registration'),
    path('', modern_home, name='modern_home'),
    path('logout/', auth_views.LogoutView.as_view(next_page='accounts:login'), name='logout'),
    path('club-admin/add-player/', views.club_admin_add_player, name='club_admin_add_player'),
    path('admin-add-referee/', views_admin_referees.admin_add_referee, name='admin_add_referee'),
    path('club-invoices/', views.club_invoices, name='club_invoices'),

    # AJAX views
    path('ajax/get-regions-for-province/', views.get_regions_for_province, name='get_regions_for_province'),
    path('ajax/get-lfas-for-region/', views.get_lfas_for_region, name='get_lfas_for_region'),
    path('ajax/get-clubs-for-lfa/', views.get_clubs_for_lfa, name='get_clubs_for_lfa'),
    path('ajax/check-id-number/', views.check_id_number, name='check_id_number'),
    path('ajax/extract-id-data/', views.ajax_extract_id_data, name='ajax_extract_id_data'),
    path('ajax/dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    path('ajax/search-members/', views.search_members_api, name='search_members_api'),
    path('ajax/quick-approve-member/', views.quick_approve_member, name='quick_approve_member'),
    path('ajax/mark-notification-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('ajax/get-organization-types/', views.get_organization_types_api, name='get_organization_types_api'),
    path('ajax/get-positions-for-org-type/', views.get_positions_for_org_type_api, name='get_positions_for_org_type_api'),

    # Utility views
    path('switch-organization/', views.switch_organization, name='switch_organization'),
    path('notifications/', views.notification_center, name='notification_center'),
    path('health-check/', views.health_check, name='health_check'),
    path('member-approvals/', views.member_approvals_list, name='member_approvals_list'),
    path('member-approvals/<int:member_id>/reject/', views.reject_member, name='reject_member'),
    path('advanced-search/', views.advanced_search, name='advanced_search'),
    path('statistics/', views.statistics, name='statistics'),

    # API views (placeholders)
    path('api/members/eligible-clubs/', views.eligible_clubs_api, name='eligible_clubs_api'),
    path('api/members/', views.members_api, name='members_api'),
    path('api/self-registration/register-member/', views.self_register_member_api, name='self_register_member_api'),
    path('api/transfers/', views.transfers_api, name='transfers_api'),
    path('api/transfers/<int:transfer_id>/approve/', views.approve_transfer_api, name='approve_transfer_api'),
    path('api/members/<int:member_id>/season-history/', views.member_season_history_api, name='member_season_history_api'),
    path('api/member-history/by-club/', views.member_history_by_club_api, name='member_history_by_club_api'),
    path('api/reports/seasonal-analysis/', views.seasonal_analysis_api, name='seasonal_analysis_api'),
    path('api/members/<int:member_id>/associations/', views.member_associations_api, name='member_associations_api'),

    # Contact support
    path('contact-support/', views.contact_support, name='contact_support'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'), # Added this line
    path('my-card/', generate_digital_card, name='digital_card'),
    path('my-invoices/', views.my_invoices, name='my_invoices'),
    path('invoice/<uuid:invoice_uuid>/', views.invoice_detail, name='invoice_detail'),
    path('registration-portal/', views.registration_portal, name='registration_portal'),
    path('update-profile-photo/', views.update_profile_photo, name='update_profile_photo'),
    path('senior-membership-dashboard/', views.senior_membership_dashboard, name='senior_membership_dashboard'),

    # National Admin Dashboard
    path('national-admin-dashboard/', views.national_admin_dashboard, name='national_admin_dashboard'),
    path('national-finance-dashboard/', views.national_finance_dashboard, name='national_finance_dashboard'),
    path('provincial-admin-dashboard/', views.provincial_admin_dashboard, name='provincial_admin_dashboard'),
    path('regional-admin-dashboard/', views.regional_admin_dashboard, name='regional_admin_dashboard'),
    path('lfa-admin-dashboard/', views.lfa_admin_dashboard, name='lfa_admin_dashboard'),
    path('club-admin-dashboard/', views.club_admin_dashboard, name='club_admin_dashboard'),
    path('association-admin-dashboard/', views.association_admin_dashboard, name='association_admin_dashboard'),
    path('member-cards-admin/', views.member_cards_admin, name='member_cards_admin'), # New link for Member Cards Admin
    path('edit-player/<int:player_id>/', views.edit_player, name='edit_player'),
    path('approve-player/<int:player_id>/', views.approve_player, name='approve_player'),
    path('club-management-dashboard/', views.club_management_dashboard, name='club_management_dashboard'),
    path('add-club-administrator/', views.add_club_administrator, name='add_club_administrator'),
    path('province-compliance/', views.province_compliance_view, name='province_compliance_view'),
    path('region-compliance/', views.region_compliance_view, name='region_compliance_view'),
    path('lfa-compliance/', views.lfa_compliance_view, name='lfa_compliance_view'),
    path('association-compliance/', views.association_compliance_view, name='association_compliance_view'),
    path('club-compliance/', views.club_compliance_view, name='club_compliance_view'),
    path('update-organization-status/', views.update_organization_status, name='update_organization_status'),

    # API endpoints for registration form
    path('api/organization-type-name/<int:org_type_id>/', views.get_organization_type_name, name='get_organization_type_name'),
    path('api/regions-for-province/<int:province_id>/', views.get_regions_for_province, name='get_regions_for_province'),
    path('api/lfas-for-region/<int:region_id>/', views.get_lfas_for_region, name='get_lfas_for_region'),
    path('api/clubs-for-lfa/<int:lfa_id>/', views.get_clubs_for_lfa, name='get_clubs_for_lfa'),
    path('ajax/check-email/', views.check_email, name='check_email'),
]