from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    WorkingLoginView, working_home, register, 
    check_username, user_qr_code, profile_view
)

app_name = 'accounts'


urlpatterns = [
    path('login/', WorkingLoginView.as_view(), name='login'),
    path('home/', working_home, name='home'),
    path('register/', register, name='register'),
    path('check-username/', check_username, name='check_username'),
    path('qr-code/', user_qr_code, name='qr_code'),
    path('profile/', profile_view, name='profile'),  # Use profile_view instead of ProfileView
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    # Add other paths as needed
]
