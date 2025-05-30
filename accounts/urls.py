from django.urls import path
from django.contrib.auth.views import LogoutView
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
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    # Add other paths as needed
]
