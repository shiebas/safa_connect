from django.urls import path
from . import views

app_name = 'registration'

urlpatterns = [
    path('senior/', views.senior_registration, name='senior_registration'),
    path('club-admin/add-player/', views.club_admin_add_player, name='club_admin_add_player'),
]