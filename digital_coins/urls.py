from django.urls import path
from . import views

app_name = 'digital_coins'

urlpatterns = [
    # ============================================================================
    # WALLET MANAGEMENT
    # ============================================================================
    path('wallet/', views.coin_wallet, name='wallet'),
    path('transactions/', views.transaction_history, name='transaction_history'),
    
    # ============================================================================
    # COIN TRANSFERS
    # ============================================================================
    path('send/', views.send_coins, name='send_coins'),
    path('receive/', views.receive_coins, name='receive_coins'),
    
    # ============================================================================
    # REWARDS SYSTEM
    # ============================================================================
    path('claim/<uuid:reward_id>/', views.claim_reward, name='claim_reward'),
    path('claim-all/', views.claim_all_rewards, name='claim_all_rewards'),
    
    # ============================================================================
    # LOYALTY CONVERSION
    # ============================================================================
    path('loyalty-conversion/', views.loyalty_conversion, name='loyalty_conversion'),
    
    # ============================================================================
    # GAMING COMPETITIONS
    # ============================================================================
    path('competitions/', views.competitions_list, name='competitions'),
    path('competition/<int:competition_id>/', views.competition_detail, name='competition_detail'),
    path('competition/<int:competition_id>/join/', views.join_competition, name='join_competition'),
    
    # ============================================================================
    # API ENDPOINTS
    # ============================================================================
    path('api/wallet-balance/', views.api_wallet_balance, name='api_wallet_balance'),
    path('api/recent-transactions/', views.api_recent_transactions, name='api_recent_transactions'),
    path('api/search-users/', views.api_search_users, name='api_search_users'),
]
