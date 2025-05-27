from django.urls import path
from .views import WorkingLoginView, working_home, register, check_username, user_qr_code
from django.contrib.auth.views import LogoutView

app_name = 'accounts'

urlpatterns = [
    path('login/', WorkingLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', register, name='register'),
    path('check-username/', check_username, name='check_username'),
    path('qr-code/', user_qr_code, name='user_qr_code'),
    path('qr-code/<int:user_id>/', user_qr_code, name='user_qr_code_with_id'),
    path('', working_home, name='home'),
]
