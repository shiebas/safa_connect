"""
Mobile App API URLs for SAFA Connect
URL patterns for mobile application endpoints
"""

from django.urls import path
from . import api_views

app_name = 'mobile_api'

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', api_views.MobileLoginView.as_view(), name='mobile_login'),
    path('auth/logout/', api_views.MobileLogoutView.as_view(), name='mobile_logout'),
    
    # User profile endpoints
    path('user/profile/', api_views.MobileUserProfileView.as_view(), name='mobile_user_profile'),
    path('user/change-password/', api_views.mobile_change_password, name='mobile_change_password'),
    
    # Member endpoints
    path('member/profile/', api_views.MobileMemberProfileView.as_view(), name='mobile_member_profile'),
    
    # Dashboard and utility endpoints
    path('dashboard/', api_views.mobile_dashboard_data, name='mobile_dashboard'),
    path('health/', api_views.mobile_health_check, name='mobile_health_check'),
]
