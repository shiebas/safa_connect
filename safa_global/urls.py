from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# Update admin site title, header, and index title
admin.site.site_header = "SAFA Administration"
admin.site.site_title = "SAFA Admin Portal"
admin.site.index_title = "Welcome to SAFA Administration Portal"


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('geography/', include('geography.urls')),
    path('membership/', include('membership.urls')),
    path('membership-cards/', include('membership_cards.urls')),
    path('league-management/', include('league_management.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),  # Add home page instead
]

# Add media files serving for development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
