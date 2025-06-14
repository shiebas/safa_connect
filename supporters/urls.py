from django.urls import path
from . import views

app_name = 'supporters'

urlpatterns = [
    path('register/', views.register_supporter, name='register'),
    path('profile/', views.supporter_profile, name='profile'),
]
