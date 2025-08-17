# membership/urls.py
from django.urls import path
from . import views
from . import invoice_views
from . import registration_views

app_name = 'membership'

urlpatterns = [
    # Invoice URLs
    path('invoices/', invoice_views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/generate/', invoice_views.generate_invoices, name='generate_invoices'),
    path('invoices/<uuid:uuid>/', invoice_views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<uuid:uuid>/pdf/', invoice_views.InvoicePDFView.as_view(), name='invoice_pdf'),
    path('invoices/<uuid:uuid>/pay/', invoice_views.mark_invoice_paid, name='mark_invoice_paid'),
    path('invoices/export/<str:format>/', invoice_views.export_invoices, name='export_invoices'),
    path('reports/outstanding/', invoice_views.OutstandingReportView.as_view(), name='outstanding_report'),

    path('register/', views.registration_portal, name='registration_portal'),
    path('register/player/', views.PlayerRegistrationView.as_view(), name='player_registration'),
    path('register/official/', views.OfficialRegistrationView.as_view(), name='official_registration'),
    path('register/admin/', views.AdminRegistrationView.as_view(), name='admin_registration'),
    path('register/success/', views.registration_success, name='registration_success'),
    path('member-approvals/', views.MemberApprovalListView.as_view(), name='member_approval_list'),
    path('member-approvals/<int:member_id>/approve/', views.approve_member, name='approve_member'),
    path('member-approvals/<int:member_id>/reject/', views.reject_member, name='reject_member'),
    path('card/<int:member_id>/', views.generate_membership_card, name='generate_membership_card'),

    # Registration AJAX
    path('club-info/', registration_views.get_club_info, name='club_info'),
]
