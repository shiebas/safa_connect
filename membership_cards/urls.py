from django.urls import path, include
from . import views
from .card_views import (
    my_digital_card, download_my_card, card_preview_image,
    admin_card_management, admin_generate_card, admin_bulk_generate_cards,
    admin_card_preview, card_verification, admin_select_for_printing,
    admin_generate_print_sheet
)
from rest_framework import routers
from .views import DigitalCardViewSet

app_name = 'membership_cards'

router = routers.DefaultRouter()
router.register(r'digitalcards', DigitalCardViewSet)

urlpatterns = [
    # User card access
    path('my-card/', my_digital_card, name='my_card'),
    path('download/<str:format_type>/', download_my_card, name='download_my_card'),
    path('preview-image/', card_preview_image, name='card_preview_image'),
    
    # Admin management
    path('admin/', admin_card_management, name='admin_management'),
    path('admin/generate/<int:member_id>/', admin_generate_card, name='admin_generate_card'),
    path('admin/bulk-generate/', admin_bulk_generate_cards, name='admin_bulk_generate'),
    path('admin/preview/<int:member_id>/', admin_card_preview, name='admin_card_preview'),
    path('admin/print-sheet/', admin_select_for_printing, name='admin_select_for_printing'),
    path('admin/generate-print-sheet/', admin_generate_print_sheet, name='admin_generate_print_sheet'),
    
    # Card verification
    path('verify/<str:safa_id>/', card_verification, name='card_verification'),

    # Data Export
    path('export/csv/', views.export_cards_csv, name='export_cards_csv'),
    
    # Legacy URLs (kept for backward compatibility)
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
