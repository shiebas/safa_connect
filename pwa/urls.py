from django.urls import path
from . import views

app_name = 'pwa'

urlpatterns = [
    # PWA essential files
    path('manifest.json', views.manifest, name='manifest'),
    path('sw.js', views.service_worker, name='service_worker'),
    path('offline/', views.offline, name='offline'),
    
    # PWA tracking and management
    path('install/', views.track_install, name='track_install'),
    path('sync-status/', views.sync_status, name='sync_status'),
    path('info/', views.pwa_info, name='info'),
]
