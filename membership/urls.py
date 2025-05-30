from django.urls import path
from . import views, registration_views, transfer_views, appeal_views
from .views import MembershipListView, MembershipCreateView, MembershipDetailView, MembershipUpdateView, MembershipDeleteView

app_name = 'membership'

urlpatterns = [
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
    path('register/player/', registration_views.PlayerRegistrationView.as_view(), 
         name='player_registration'),
    path('register/payment/', registration_views.PaymentSelectionView.as_view(), 
         name='payment_selection'),
    path('register/confirm/', registration_views.PaymentConfirmationView.as_view(), 
         name='payment_confirmation'),
    
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
    path('appeals/federation/history/', appeal_views.FederationAppealHistoryView.as_view(), name='federation_appeal_history'),


  # Membership
    path('memberships/', MembershipListView.as_view(), name='membership-list'),
    path('memberships/add/', MembershipCreateView.as_view(), name='membership-create'),
    path('memberships/<int:pk>/', MembershipDetailView.as_view(), name='membership-detail'),
    path('memberships/<int:pk>/edit/', MembershipUpdateView.as_view(), name='membership-update'),
    path('memberships/<int:pk>/delete/', MembershipDeleteView.as_view(), name='membership-delete'),
]