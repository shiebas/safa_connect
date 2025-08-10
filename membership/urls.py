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
]
