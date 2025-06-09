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
    path('admin/logout/', auth_views.LogoutView.as_view(next_page='/'), name='admin_logout'),
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),  # Add this back
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),  # Django-allauth URLs
    path('geography/', include('geography.urls')),
    path('membership/', include('membership.urls')),
    path('cards/', include('membership_cards.urls')),
    
    # Password reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
