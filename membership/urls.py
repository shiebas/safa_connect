# membership/urls.py
from django.urls import path
from . import views

app_name = 'membership'

urlpatterns = [
    path('register/', views.registration_portal, name='registration_portal'),
    path('register/player/', views.PlayerRegistrationView.as_view(), name='player_registration'),
    path('register/official/', views.OfficialRegistrationView.as_view(), name='official_registration'),
    path('register/admin/', views.AdminRegistrationView.as_view(), name='admin_registration'),
    path('register/success/', views.registration_success, name='registration_success'),
    path('member-approvals/', views.MemberApprovalListView.as_view(), name='member_approval_list'),
    path('member-approvals/<int:member_id>/approve/', views.approve_member, name='approve_member'),
    path('member-approvals/<int:member_id>/reject/', views.reject_member, name='reject_member'),
]
