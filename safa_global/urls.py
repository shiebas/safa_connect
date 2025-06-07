from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# Updated Wagtail imports
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail import urls as wagtail_urls  # Changed from wagtail.core


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('accounts/', include('accounts.urls')),  # This includes your accounts URLs with namespace
    path('accounts/', include('allauth.urls')),  # Django-allauth URLs
    path('geography/', include('geography.urls')),
    path('membership/', include('membership.urls')),
    path('competitions/', include(('competitions.urls', 'competitions'), namespace='competitions')),

    # Wagtail admin and URLs
    path('cms/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    path('pages/', include(wagtail_urls)),

    # Your other URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Add this to your main URLs file
if 'tools' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('admin/tools/', include('tools.urls', namespace='tools')),
    ]
