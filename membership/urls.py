from django.urls import path, include
from . import views, registration_views, transfer_views, appeal_views, invoice_views, api_views
from . import outstanding_report, membership_registration_views, junior_registration_views
from .views import MembershipListView, MembershipCreateView, MembershipDetailView, MembershipUpdateView, MembershipDeleteView
from rest_framework import routers
from .views import MemberViewSet

app_name = 'membership'

router = routers.DefaultRouter()
router.register(r'members', MemberViewSet)

urlpatterns = [
    # Registration Type Selector (MAIN ENTRY POINT)
    path('', views.registration_selector, name='registration_selector'),

    # Senior Registration
    path('senior/', views.senior_registration, name='senior_registration'),

    # Junior Registration
    path('junior/', junior_registration_views.JuniorRegistrationView.as_view(), name='junior_registration'),
    path('junior/register/', junior_registration_views.JuniorRegistrationView.as_view(),
         name='junior_registration_alt'),
    path('junior/register/success/', junior_registration_views.JuniorRegistrationSuccessView.as_view(),
         name='junior_registration_success'),

    # Member and Player Management
    path('members/', views.MemberListView.as_view(), name='member_list'),
    path('members/add/', views.MemberCreateView.as_view(), name='member_create'),
    path('members/<int:pk>/edit/', views.MemberUpdateView.as_view(), name='member_update'),
    path('players/', views.PlayerListView.as_view(), name='player_list'),
    path('players/add/', views.PlayerCreateView.as_view(), name='player_create'),
    path('players/<int:pk>/edit/', views.PlayerUpdateView.as_view(), name='player_update'),

    # Club Management
    path('clubs/', views.ClubListView.as_view(), name='club_list'),
    path('clubs/add/', views.ClubCreateView.as_view(), name='club_create'),
    path('clubs/<int:pk>/', views.ClubDetailView.as_view(), name='club_detail'),
    path('clubs/<int:pk>/edit/', views.ClubUpdateView.as_view(), name='club_update'),

    # Registration Flow
    path('register/player/', registration_views.PlayerRegistrationView.as_view(), name='player_registration'),
    path('register/payment/', registration_views.PaymentSelectionView.as_view(), name='payment_selection'),
    path('register/confirm/', registration_views.PaymentConfirmationView.as_view(), name='payment_confirmation'),

    # Transfer Management
    path('transfers/', transfer_views.TransferListView.as_view(), name='transfer_list'),
    path('transfers/request/', transfer_views.TransferRequestView.as_view(), name='transfer_request'),
    path('transfers/<int:pk>/', transfer_views.TransferDetailView.as_view(), name='transfer_detail'),
    path('transfers/<int:pk>/approve/', transfer_views.TransferApproveView.as_view(), name='transfer_approve'),
    path('transfers/<int:pk>/reject/', transfer_views.TransferRejectView.as_view(), name='transfer_reject'),

    # Appeal Management
    path('appeals/', appeal_views.AppealListView.as_view(), name='appeal_list'),
    path('appeals/review/', appeal_views.ReviewAppealListView.as_view(), name='review_appeals'),
    path('appeals/create/<int:transfer_id>/', appeal_views.AppealCreateView.as_view(), name='appeal_create'),
    path('appeals/<int:pk>/', appeal_views.AppealDetailView.as_view(), name='appeal_detail'),
    path('appeals/<int:pk>/review/', appeal_views.AppealReviewView.as_view(), name='appeal_review'),
    path('appeals/federation/', appeal_views.FederationAppealListView.as_view(), name='federation_appeals'),
    path('appeals/federation/history/', appeal_views.FederationAppealHistoryView.as_view(),
         name='federation_appeal_history'),

    # Membership
    path('memberships/', MembershipListView.as_view(), name='membership-list'),
    path('memberships/add/', MembershipCreateView.as_view(), name='membership-create'),
    path('memberships/<int:pk>/', MembershipDetailView.as_view(), name='membership-detail'),
    path('memberships/<int:pk>/edit/', MembershipUpdateView.as_view(), name='membership-update'),
    path('memberships/<int:pk>/delete/', MembershipDeleteView.as_view(), name='membership-delete'),

    # Payment and Invoices
    path('register/success/', registration_views.RegistrationSuccessView.as_view(), name='registration_success'),
    path('register/payment/return/', views.PaymentReturnView.as_view(), name='payment_return'),
    path('register/payment/cancel/', views.PaymentCancelView.as_view(), name='payment_cancel'),

    # Invoice Management
    path('invoices/', invoice_views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/<uuid:uuid>/', invoice_views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<uuid:uuid>/pdf/', invoice_views.InvoicePDFView.as_view(), name='invoice_pdf'),
    path('invoices/<uuid:uuid>/mark-paid/', invoice_views.mark_invoice_paid, name='mark_invoice_paid'),
    path('invoices/export/<str:format>/', invoice_views.export_invoices, name='export_invoices'),
    path('payments/<uuid:uuid>/process/', views.ProcessCardPaymentView.as_view(), name='process_card_payment'),

    # Reports
    path('reports/outstanding-balance/', invoice_views.OutstandingReportView.as_view(), name='outstanding_report'),
    path('reports/outstanding-balance/export/<str:format>/', outstanding_report.export_outstanding_report, name='export_outstanding_report'),
    path('reports/payment-reminders/<str:entity_type>/<int:entity_id>/', views.send_payment_reminder, name='send_payment_reminder'),

    # New Two-Tier Membership System
    path('apply/', membership_registration_views.membership_application, name='membership_application'),
    path('apply/submitted/', membership_registration_views.ApplicationSubmittedView.as_view(), name='application_submitted'),
    path('admin/pending/', membership_registration_views.membership_dashboard, name='pending_applications'),
    path('admin/approve/<int:member_id>/', membership_registration_views.approve_member, name='approve_member'),
    path('admin/reject/<int:member_id>/', membership_registration_views.reject_member, name='reject_member'),
    path('admin/dashboard/', membership_registration_views.membership_dashboard, name='membership_dashboard'),
    path('club-registration/<int:member_id>/', membership_registration_views.register_with_club, name='register_with_club'),
    path('check-status/', membership_registration_views.check_member_status, name='check_member_status'),

    # Legacy membership application (keeping for compatibility)
    path('membership-application/', views.membership_application, name='legacy_membership_application'),

    # API and other endpoints
    path('api/', include(router.urls)),
    path('api/regions_by_province/<int:province_id>/', api_views.regions_by_province, name='regions_by_province'),
    path('api/lfas_by_region/<int:region_id>/', api_views.lfas_by_region, name='lfas_by_region'),
    path('api/clubs_by_lfa/<int:lfa_id>/', api_views.clubs_by_lfa, name='clubs_by_lfa'),
    path('verify/', views.verify_view, name='verify'),
]
