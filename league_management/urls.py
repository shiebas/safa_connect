from django.urls import path
from . import views

app_name = 'league_management'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('competition/<uuid:competition_id>/', views.competition_detail, name='competition_detail'),
    path('statistics/<uuid:competition_id>/', views.league_statistics, name='league_statistics'),
    path('statistics/<uuid:competition_id>/<uuid:group_id>/', views.league_statistics, name='group_statistics'),
    path('team/<uuid:competition_id>/<uuid:team_id>/', views.team_statistics, name='team_statistics'),
]
