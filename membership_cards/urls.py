from django.urls import path, include
from . import views
from rest_framework import routers
from .views import DigitalCardViewSet

app_name = 'membership_cards'

router = routers.DefaultRouter()
router.register(r'digitalcards', DigitalCardViewSet)

urlpatterns = [
    path('my-card/', views.my_digital_card, name='my_card'),
    path('qr-code/', views.card_qr_code, name='qr_code'),
    path('verify/', views.verify_qr_code, name='verify_qr'),
    path('download/', views.download_card, name='download_card'),
    path('test-generate/', views.test_card_generation, name='test_generate'),
    path('debug-qr/', views.debug_qr_data, name='debug_qr'),
    path('test-qr-decode/', views.test_qr_decode, name='test_qr_decode'),
    path('force-regenerate/', views.force_regenerate_qr, name='force_regenerate'),
    path('dashboard/', views.system_dashboard, name='dashboard'),
    path('google-wallet/', views.add_to_google_wallet, name='google_wallet'),
    path('api/', include(router.urls)),
]
