from django.urls import path, include
from rest_framework import routers
from . import views
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
]
