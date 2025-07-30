# membership/urls.py - CORRECTED VERSION
# Updated to work with the new SAFA membership system

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views
from .views import RegistrationSelectorView
from .admin_views import (
    national_admin_dashboard, financial_dashboard, member_statistics,
    season_management, member_approval_queue, invoice_management,
    transfer_management, workflow_monitoring, system_health_check,
    ajax_member_search, ajax_invoice_details
)

app_name = 'membership'

# DRF Router for API endpoints
router = DefaultRouter()
router.register(r'members', views.MemberViewSet, basename='member')
router.register(r'invoices', api_views.InvoiceViewSet, basename='invoice')
router.register(r'transfers', api_views.TransferViewSet, basename='transfer')
router.register(r'seasons', api_views.SeasonConfigViewSet, basename='season')

urlpatterns = [
    # ========================================================================
    # MAIN REGISTRATION ENTRY POINTS
    # ========================================================================
    
    # Main registration selector
    path('', views.RegistrationSelectorView.as_view(), name='registration_selector'),
    
    # Member registration (unified system)
    path('register/', views.MemberRegistrationView.as_view(), name='member_registration'),
    path('register/success/', views.RegistrationSuccessView.as_view(), name='registration_success'),
    path('register/status/', views.RegistrationStatusView.as_view(), name='registration_status'),
    
    # Member management
    path('members/', views.MemberListView.as_view(), name='member_list'),
    path('members/create/', views.MemberCreateView.as_view(), name='member_create'),
    path('members/<int:pk>/', views.MemberDetailView.as_view(), name='member_detail'),
    path('members/<int:pk>/edit/', views.MemberUpdateView.as_view(), name='member_update'),
    path('members/<int:pk>/approve/', views.MemberApproveView.as_view(), name='member_approve'),
    path('members/<int:pk>/reject/', views.MemberRejectView.as_view(), name='member_reject'),
    path('members/<int:pk>/documents/', views.MemberDocumentListView.as_view(), name='member_documents'),
    path('members/<int:pk>/history/', views.MemberHistoryView.as_view(), name='member_history'),
    
    # ========================================================================
    # TRANSFER MANAGEMENT
    # ========================================================================
    
    path('transfers/', views.TransferListView.as_view(), name='transfer_list'),
    path('transfers/request/', views.TransferRequestView.as_view(), name='transfer_request'),
    path('transfers/<int:pk>/', views.TransferDetailView.as_view(), name='transfer_detail'),
    path('transfers/<int:pk>/approve/', views.TransferApproveView.as_view(), name='transfer_approve'),
    path('transfers/<int:pk>/reject/', views.TransferRejectView.as_view(), name='transfer_reject'),
    
    # ========================================================================
    # INVOICE AND PAYMENT MANAGEMENT
    # ========================================================================
    
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/<uuid:uuid>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<uuid:uuid>/pdf/', views.InvoicePDFView.as_view(), name='invoice_pdf'),
    path('invoices/<uuid:uuid>/pay/', views.InvoicePaymentView.as_view(), name='invoice_payment'),
    path('invoices/<uuid:uuid>/mark-paid/', views.MarkInvoicePaidView.as_view(), name='mark_invoice_paid'),
    
    # Payment processing
    path('payments/process/', views.ProcessPaymentView.as_view(), name='process_payment'),
    path('payments/return/', views.PaymentReturnView.as_view(), name='payment_return'),
    path('payments/cancel/', views.PaymentCancelView.as_view(), name='payment_cancel'),
    path('payments/notify/', views.PaymentNotifyView.as_view(), name='payment_notify'),
    
    # ========================================================================
    # DOCUMENT MANAGEMENT
    # ========================================================================
    
    path('documents/', views.DocumentListView.as_view(), name='document_list'),
    path('documents/upload/', views.DocumentUploadView.as_view(), name='document_upload'),
    path('documents/<int:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
    path('documents/<int:pk>/approve/', views.DocumentApproveView.as_view(), name='document_approve'),
    path('documents/<int:pk>/reject/', views.DocumentRejectView.as_view(), name='document_reject'),
    
    # ========================================================================
    # SEASON MANAGEMENT (Admin Only)
    # ========================================================================
    
    path('seasons/', views.SeasonListView.as_view(), name='season_list'),
    path('seasons/create/', views.SeasonCreateView.as_view(), name='season_create'),
    path('seasons/<int:pk>/', views.SeasonDetailView.as_view(), name='season_detail'),
    path('seasons/<int:pk>/activate/', views.SeasonActivateView.as_view(), name='season_activate'),
    path('seasons/<int:pk>/fees/', views.SeasonFeeStructureView.as_view(), name='season_fees'),
    
    # ========================================================================
    # REPORTS AND ANALYTICS
    # ========================================================================
    
    path('reports/', views.ReportsIndexView.as_view(), name='reports_index'),
    path('reports/members/', views.MemberReportView.as_view(), name='member_report'),
    path('reports/invoices/', views.InvoiceReportView.as_view(), name='invoice_report'),
    path('reports/transfers/', views.TransferReportView.as_view(), name='transfer_report'),
    path('reports/outstanding/', views.OutstandingReportView.as_view(), name='outstanding_report'),
    path('reports/export/<str:report_type>/', views.ExportReportView.as_view(), name='export_report'),
    
    # ========================================================================
    # ADMIN DASHBOARDS
    # ========================================================================
    
    path('admin/dashboard/', national_admin_dashboard, name='admin_dashboard'),
    path('admin/dashboard/financial/', financial_dashboard, name='financial_dashboard'),
    path('admin/dashboard/members/', member_statistics, name='member_statistics'),
    path('admin/dashboard/seasons/', season_management, name='season_management'),
    path('admin/dashboard/approvals/', member_approval_queue, name='member_approvals'),
    path('admin/dashboard/invoices/', invoice_management, name='invoice_management'),
    path('admin/dashboard/transfers/', transfer_management, name='transfer_management'),
    path('admin/dashboard/workflows/', workflow_monitoring, name='workflow_monitoring'),
    path('admin/dashboard/health/', system_health_check, name='system_health'),
    
    # ========================================================================
    # AJAX AND API ENDPOINTS
    # ========================================================================
    
    # Geographic API endpoints
    path('api/geography/regions/<int:province_id>/', api_views.regions_by_province, name='regions_by_province'),
    path('api/geography/lfas/<int:region_id>/', api_views.lfas_by_region, name='lfas_by_region'),
    path('api/geography/clubs/<int:lfa_id>/', api_views.clubs_by_lfa, name='clubs_by_lfa'),
    path('api/geography/clubs/search/', api_views.club_search, name='club_search'),
    
    # Member API endpoints
    path('api/members/search/', api_views.member_search, name='member_search'),
    path('api/members/validate-id/', api_views.validate_id_number, name='validate_id_number'),
    path('api/members/check-email/', api_views.check_email_availability, name='check_email'),
    
    # AJAX endpoints for admin interface
    path('ajax/member-search/', ajax_member_search, name='ajax_member_search'),
    path('ajax/invoice-details/<int:invoice_id>/', ajax_invoice_details, name='ajax_invoice_details'),
    path('ajax/workflow-progress/', api_views.workflow_progress, name='ajax_workflow_progress'),
    
    # Fee calculation
    path('api/fees/calculate/', api_views.calculate_fees, name='calculate_fees'),
    
    # Dashboard data endpoints
    path('api/dashboard/stats/', api_views.dashboard_stats, name='dashboard_stats'),
    path('api/dashboard/charts/', api_views.dashboard_charts, name='dashboard_charts'),
    
    # ========================================================================
    # BULK OPERATIONS
    # ========================================================================
    
    path('bulk/approve/', views.BulkApproveView.as_view(), name='bulk_approve'),
    path('bulk/reject/', views.BulkRejectView.as_view(), name='bulk_reject'),
    path('bulk/invoices/', views.BulkInvoiceView.as_view(), name='bulk_invoices'),
    path('bulk/reminders/', views.BulkReminderView.as_view(), name='bulk_reminders'),
    
    # ========================================================================
    # WORKFLOW AND STATUS TRACKING
    # ========================================================================
    
    path('workflow/<int:member_id>/', views.WorkflowDetailView.as_view(), name='workflow_detail'),
    path('workflow/<int:member_id>/update/', views.WorkflowUpdateView.as_view(), name='workflow_update'),
    path('status/check/', views.StatusCheckView.as_view(), name='status_check'),
    
    # ========================================================================
    # NOTIFICATIONS AND COMMUNICATIONS
    # ========================================================================
    
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/send/', views.SendNotificationView.as_view(), name='send_notification'),
    path('reminders/payment/', views.PaymentReminderView.as_view(), name='payment_reminder'),
    
    # ========================================================================
    # REST API
    # ========================================================================
    
    path('api/v1/', include(router.urls)),
    path('api/v1/auth/', include('rest_framework.urls')),
    
    # ========================================================================
    # LEGACY COMPATIBILITY (Keep for migration period)
    # ========================================================================
    
    # Legacy senior registration (redirect to new system)
    path('senior/', views.LegacyRedirectView.as_view(), {'target': 'member_registration'}, name='senior_registration'),
    path('junior/', views.LegacyRedirectView.as_view(), {'target': 'member_registration'}, name='junior_registration'),
    
    # Legacy membership application (redirect)
    path('apply/', views.LegacyRedirectView.as_view(), {'target': 'member_registration'}, name='membership_application'),
    path('membership-application/', views.LegacyRedirectView.as_view(), {'target': 'member_registration'}, name='legacy_membership_application'),
    
    # ========================================================================
    # UTILITY ENDPOINTS
    # ========================================================================
    
    path('health/', views.HealthCheckView.as_view(), name='health_check'),
    path('version/', views.VersionView.as_view(), name='version'),
    path('test-email/', views.TestEmailView.as_view(), name='test_email'),
]