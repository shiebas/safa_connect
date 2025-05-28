from django.urls import path
from . import views, registration_views, transfer_views, appeal_views

app_name = 'membership'

urlpatterns = [
    # Member and Player CRUD
    path('members/', views.MemberListView.as_view(), name='member-list'),
    path('members/add/', views.MemberCreateView.as_view(), name='member-create'),
    path('members/<int:pk>/edit/', views.MemberUpdateView.as_view(), name='member-update'),
    path('players/', views.PlayerListView.as_view(), name='player-list'),
    path('players/add/', views.PlayerCreateView.as_view(), name='player-create'),
    path('players/<int:pk>/edit/', views.PlayerUpdateView.as_view(), name='player-update'),
    
    # Registration flow
    path('register/player/', registration_views.PlayerRegistrationView.as_view(), 
         name='player_registration'),
    path('register/payment/', registration_views.PaymentSelectionView.as_view(), 
         name='payment_selection'),
    path('register/confirm/', registration_views.PaymentConfirmationView.as_view(), 
         name='payment_confirmation'),
    path('register/success/', registration_views.RegistrationSuccessView.as_view(), 
         name='registration_success'),
    
    # Transfer management
    path('transfers/', transfer_views.TransferListView.as_view(), name='transfer_list'),
    path('transfers/request/', transfer_views.TransferRequestView.as_view(), name='transfer_request'),
    path('transfers/<int:pk>/', transfer_views.TransferDetailView.as_view(), name='transfer_detail'),
    
    # AJAX endpoints
    path('api/club-info/', registration_views.get_club_info, name='club_info'),

    # Appeal URLs
    path('appeals/', 
         appeal_views.AppealListView.as_view(), 
         name='appeal_list'),
    path('appeals/create/<int:transfer_id>/', 
         appeal_views.AppealCreateView.as_view(), 
         name='appeal_create'),
    path('appeals/<int:pk>/', 
         appeal_views.AppealDetailView.as_view(), 
         name='appeal_detail'),
    path('appeals/<int:pk>/review/', 
         appeal_views.AppealReviewView.as_view(), 
         name='appeal_review'),
]
