from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from geography.views import advanced_home


urlpatterns = [
    path("admin/", admin.site.urls),
    path('geography/', include('geography.urls', namespace='geography')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('accounts/', include('allauth.urls')),
    path('', advanced_home, name='home'),
  

    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
      + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)











 