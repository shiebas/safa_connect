from django.urls import path
from . import views

app_name = 'membership_cards'

urlpatterns = [
    path('my-card/', views.my_digital_card, name='my_card'),
    path('qr-code/', views.card_qr_code, name='qr_code'),
    path('verify/', views.verify_qr_code, name='verify_qr'),
    path('download/', views.download_card, name='download_card'),
    path('test-generate/', views.test_card_generation, name='test_generate'),
    path('debug-qr/', views.debug_qr_data, name='debug_qr'),  # Add this
    path('test-qr-decode/', views.test_qr_decode, name='test_qr_decode'),
    path('force-regenerate/', views.force_regenerate_qr, name='force_regenerate'),
    path('dashboard/', views.system_dashboard, name='dashboard'),
]
