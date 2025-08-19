# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, views_admin_referees
from .views import modern_home

app_name = 'accounts'

urlpatterns = [
    path('national-registration/', views.national_registration, name='national_registration'),
    path('', modern_home, name='home'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('club-admin/add-player/', views.club_admin_add_player, name='club_admin_add_player'),
    path('admin-add-referee/', views_admin_referees.admin_add_referee, name='admin_add_referee'),
    path('club-invoices/', views.club_invoices, name='club_invoices'),

    # AJAX views
    path('ajax/get-regions-for-province/', views.get_regions_for_province, name='get_regions_for_province'),
    path('ajax/get-lfas-for-region/', views.get_lfas_for_region, name='get_lfas_for_region'),
    path('ajax/get-clubs-for-lfa/', views.get_clubs_for_lfa, name='get_clubs_for_lfa'),
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
    path('my-invoices/', views.my_invoices, name='my_invoices'),
    path('settings/', views.settings, name='settings'),
    path('registration-portal/', views.registration_portal, name='registration_portal'),
    path('update-profile-photo/', views.update_profile_photo, name='update_profile_photo'),
    path('senior-membership-dashboard/', views.senior_membership_dashboard, name='senior_membership_dashboard'),
]