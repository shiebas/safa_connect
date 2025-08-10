# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import ModernLoginView, modern_home

app_name = 'accounts'

urlpatterns = [
    path('', modern_home, name='home'),
    path('login/', ModernLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
path('club-admin/add-player/', views.club_admin_add_player, name='club_admin_add_player'),
]

