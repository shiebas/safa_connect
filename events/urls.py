from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API routes
router = DefaultRouter()
router.register(r'stadiums', views.StadiumViewSet)
router.register(r'matches', views.InternationalMatchViewSet)
router.register(r'tickets', views.TicketViewSet)
router.register(r'groups', views.TicketGroupViewSet)

app_name = 'events'

urlpatterns = [
    # Admin dashboard
    path('dashboard/', views.events_dashboard, name='dashboard'),
    
    # Public views
    path('matches/', views.available_matches, name='available_matches'),
    path('matches/<uuid:match_id>/', views.match_detail, name='match_detail'),
    
    # API
    path('api/', include(router.urls)),
]
