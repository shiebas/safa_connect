from django.urls import path, include
from rest_framework import routers
from . import views
from .views import SupporterProfileViewSet

app_name = 'supporters'

router = routers.DefaultRouter()
router.register(r'supporterprofiles', SupporterProfileViewSet)

urlpatterns = [
    path('register/', views.register_supporter, name='register'),
    path('profile/', views.supporter_profile, name='profile'),
    path('api/', include(router.urls)),
]
