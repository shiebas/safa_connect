from django.urls import path
from .views import WorkingLoginView, working_home

app_name = 'accounts'  # Add this line at the top

urlpatterns = [
    path('login/', WorkingLoginView.as_view(), name='login'),
    path('', working_home, name='home'),  # This line MUST say name='home'
]