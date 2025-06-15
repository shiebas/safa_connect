from django.urls import path, include
from rest_framework import routers
from . import views
from .views import CompetitionViewSet

app_name = 'competitions'  # This is the important line to add

router = routers.DefaultRouter()
router.register(r'competitions', CompetitionViewSet)

urlpatterns = [
    # Your URL patterns here
    # For example:
    # path('', views.CompetitionListView.as_view(), name='competition-list'),
    # path('create/', views.CompetitionCreateView.as_view(), name='competition-create'),
    # path('<int:pk>/', views.CompetitionDetailView.as_view(), name='competition-detail'),
    path('api/', include(router.urls)),
]