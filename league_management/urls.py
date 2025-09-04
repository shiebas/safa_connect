from django.urls import path, include
from rest_framework import routers
from . import views
from . import team_sheet_views
from .views import CompetitionCategoryViewSet, CompetitionViewSet

app_name = 'league_management'

router = routers.DefaultRouter()
router.register(r'competitioncategories', CompetitionCategoryViewSet)
router.register(r'competitions', CompetitionViewSet)

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('competition/<uuid:competition_id>/', views.competition_detail, name='competition_detail'),
    path('statistics/<uuid:competition_id>/', views.league_statistics, name='league_statistics'),
    path('statistics/<uuid:competition_id>/<uuid:group_id>/', views.league_statistics, name='group_statistics'),
    path('team/<uuid:competition_id>/<uuid:team_id>/', views.team_statistics, name='team_statistics'),
    path('api/', include(router.urls)),
    path('fixture-generation/', views.fixture_generation_view, name='fixture_generation'),
    
    # Team Sheet URLs
    path('team-sheets/<uuid:competition_id>/', team_sheet_views.team_sheet_list, name='team_sheet_list'),
    path('team-sheet/<uuid:match_id>/<uuid:team_id>/', team_sheet_views.team_sheet_detail, name='team_sheet_detail'),
    path('team-sheet/create/<uuid:match_id>/<uuid:team_id>/', team_sheet_views.team_sheet_create, name='team_sheet_create'),
    path('team-sheet/template/<uuid:match_id>/<uuid:team_id>/<uuid:template_id>/', team_sheet_views.team_sheet_from_template, name='team_sheet_from_template'),
    path('team-sheet/template/save/<uuid:match_id>/<uuid:team_id>/', team_sheet_views.team_sheet_template_save, name='team_sheet_template_save'),
    
    # Discipline and Activity URLs
    path('discipline/<uuid:competition_id>/', team_sheet_views.player_discipline_list, name='player_discipline_list'),
    path('activity-logs/', team_sheet_views.activity_logs, name='activity_logs'),
    path('activity-logs/<uuid:competition_id>/', team_sheet_views.activity_logs, name='activity_logs_competition'),
    path('match-event/<uuid:match_id>/', team_sheet_views.add_match_event, name='add_match_event'),
]
