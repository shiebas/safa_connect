from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from safa_connect.dashboard_views import (
    superuser_dashboard, user_management, edit_user, 
    delete_user, toggle_user_status
)
from accounts.views import custom_admin_logout

# Update admin site title, header, and index title
admin.site.site_header = "SAFA Administration"
admin.site.site_title = "SAFA Admin Portal"
admin.site.index_title = "Welcome to SAFA Administration Portal"

# Error handlers
handler404 = 'accounts.views.custom_404_view'
handler500 = 'accounts.views.custom_500_view'
handler403 = 'accounts.views.custom_403_view'

urlpatterns = [
    path('admin/logout/', custom_admin_logout, name='admin_logout'),
    path('admin/dashboard/', superuser_dashboard, name='superuser_dashboard'),
    path('admin/users/', user_management, name='user_management'),
    path('admin/users/<int:user_id>/edit/', edit_user, name='edit_user'),
    path('admin/users/<int:user_id>/delete/', delete_user, name='delete_user'),
    path('admin/users/<int:user_id>/toggle-status/', toggle_user_status, name='toggle_user_status'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('local-accounts/', include('accounts.urls')),
    path('geography/', include(('geography.urls', 'geography'), namespace='geography')),
    path('membership/', include('membership.urls', namespace='membership')),
    path('membership-cards/', include('membership_cards.urls')),
    path('league-management/', include('league_management.urls')),
    path('supporters/', include('supporters.urls', namespace='supporters')),
    path('events/', include('events.urls', namespace='events')),
    path('store/', include('merchandise.urls', namespace='merchandise')),
    path('pwa/', include('pwa.urls', namespace='pwa')),
    path('legal/', include('legal.urls', namespace='legal')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),  # Add home page instead
]



# Add media files serving for development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
