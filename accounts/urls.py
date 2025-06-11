from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    WorkingLoginView, working_home, register, 
    check_username, user_qr_code, profile_view, 
    model_debug_view,  # Remove generate_safa_id_ajax
    check_email_availability, check_id_number_availability,
    registration_portal, province_registration, club_registration,
    api_regions, api_clubs, national_registration, lfa_registration, api_lfas, supporter_registration,
    update_profile_photo
)

app_name = 'accounts'


urlpatterns = [
    path('', working_home, name='home'),
    path('login/', WorkingLoginView.as_view(), name='login'),
    path('home/', working_home, name='working_home'),
    path('register/', register, name='register'),  # Add this back
    path('check-username/', check_username, name='check_username'),
    path('qr-code/', user_qr_code, name='qr_code'),
    path('profile/', profile_view, name='profile'),  # Use profile_view instead of ProfileView
    path('profile/update-photo/', update_profile_photo, name='update_profile_photo'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('ajax/check-email/', check_email_availability, name='check_email'),
    path('ajax/check-id-number/', check_id_number_availability, name='check_id_number'),
    # Remove the generate-safa-id URL since we're using admin actions now
    path('registration-portal/', registration_portal, name='registration_portal'),
    path('register/province/', province_registration, name='province_registration'),
    path('api/regions/', api_regions, name='api_regions'),
    path('api/clubs/', api_clubs, name='api_clubs'),
    path('register/national/', national_registration, name='national_registration'),
    path('register/lfa/', lfa_registration, name='lfa_registration'),
    path('register/club/', club_registration, name='club_registration'),  # Keep only one
    path('register/supporter/', supporter_registration, name='supporter_registration'),
    path('api/lfas/', api_lfas, name='api_lfas'),
    
    # Add other paths as needed
]
