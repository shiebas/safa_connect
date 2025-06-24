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
    path('preferences/edit/', views.edit_preferences, name='edit_preferences'),
    path('preferences/setup/', views.preferences_setup, name='preferences_setup'),
    path('api/', include(router.urls)),
]
