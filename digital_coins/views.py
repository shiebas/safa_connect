from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Sum, Q, F
from django.core.paginator import Paginator
from django.urls import reverse
from decimal import Decimal
import json

from .models import (
    SAFACoinWallet, SAFACoinTransaction, SAFACoinTransfer,
    SAFACoinReward, SAFACoinCompetition, SAFACoinCompetitionParticipation,
    SAFACoinLoyaltyConversion
)
from django.contrib.auth import get_user_model

User = get_user_model()

# ============================================================================
# WALLET MANAGEMENT
# ============================================================================

@login_required
def coin_wallet(request):
    """Display user's SAFA Coin wallet"""
    try:
        wallet = SAFACoinWallet.objects.get(user=request.user)
    except SAFACoinWallet.DoesNotExist:
        # Create wallet for new user
        wallet = SAFACoinWallet.objects.create(user=request.user)
        # Give welcome bonus
        wallet.add_coins(Decimal('100.0'), "Welcome bonus - New SAFA member")
    
    # Get recent transactions
    transactions = SAFACoinTransaction.objects.filter(wallet=wallet).order_by('-created')[:10]
    
    # Get pending rewards
    pending_rewards = SAFACoinReward.objects.filter(
        user=request.user,
        claimed=False
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
    )
    
    # Get active competitions
    active_competitions = SAFACoinCompetition.objects.filter(status='ACTIVE')
    
    # Get user's competition participations
    user_participations = SAFACoinCompetitionParticipation.objects.filter(
        user=request.user
    ).select_related('competition').order_by('-joined_at')[:5]
    
    context = {
        'wallet': wallet,
        'transactions': transactions,
        'pending_rewards': pending_rewards,
        'active_competitions': active_competitions,
        'user_participations': user_participations,
        'total_competitions': user_participations.count(),
        'total_prizes_won': user_participations.aggregate(
            total=Sum('prizes_won')
        )['total'] or Decimal('0.0'),
    }
    
    return render(request, 'digital_coins/wallet.html', context)

@login_required
def transaction_history(request):
    """Display full transaction history"""
    try:
        wallet = request.user.coin_wallet
    except SAFACoinWallet.DoesNotExist:
        messages.error(request, "You don't have a coin wallet yet.")
        return redirect('digital_coins:wallet')
    
    # Get all transactions with pagination
    transactions = SAFACoinTransaction.objects.filter(wallet=wallet).order_by('-created')
    
    # Filter by transaction type if specified
    transaction_type = request.GET.get('transaction_type')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    # Filter by date range if specified
    date_from = request.GET.get('date_from')
    if date_from:
        transactions = transactions.filter(created__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        transactions = transactions.filter(created__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'transactions': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    
    return render(request, 'digital_coins/transaction_history.html', context)

# ============================================================================
# COIN TRANSFERS
# ============================================================================

@login_required
def send_coins(request):
    """Send coins to another user"""
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        amount = request.POST.get('amount')
        message = request.POST.get('message', '')
        
        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, TypeError):
            messages.error(request, "Please enter a valid amount.")
            return redirect('digital_coins:send_coins')
        
        # Find recipient
        try:
            recipient = User.objects.get(id=recipient_id)
            if recipient == request.user:
                messages.error(request, "You cannot send coins to yourself.")
                return redirect('digital_coins:send_coins')
        except User.DoesNotExist:
            messages.error(request, "Recipient not found.")
            return redirect('digital_coins:send_coins')
        
        # Check if sender has enough coins (including 1 coin fee)
        try:
            sender_wallet = request.user.coin_wallet
            total_cost = amount + Decimal('1.0')  # Amount + 1 coin fee
            if not sender_wallet.can_afford(total_cost):
                messages.error(request, f"Insufficient coin balance. You need {total_cost} coins (including 1 coin fee).")
                return redirect('digital_coins:send_coins')
        except SAFACoinWallet.DoesNotExist:
            messages.error(request, "You don't have a coin wallet.")
            return redirect('digital_coins:wallet')
        
        # Create transfer
        try:
            recipient_wallet = SAFACoinWallet.objects.get(user=recipient)
        except SAFACoinWallet.DoesNotExist:
            recipient_wallet = SAFACoinWallet.objects.create(user=recipient)
        
        transfer = SAFACoinTransfer.objects.create(
            from_wallet=sender_wallet,
            to_wallet=recipient_wallet,
            amount=amount,
            message=message
        )
        
        # Execute transfer
        if transfer.execute_transfer():
            messages.success(request, f"Successfully sent {amount} SAFA Coins to {recipient.get_full_name()}.")
        else:
            messages.error(request, "Transfer failed. Please try again.")
        
        return redirect('digital_coins:wallet')
    
    # Get user's wallet for balance display
    try:
        wallet = request.user.coin_wallet
    except SAFACoinWallet.DoesNotExist:
        wallet = None
    
    context = {
        'wallet': wallet,
    }
    
    return render(request, 'digital_coins/send_coins.html', context)

@login_required
def receive_coins(request):
    """Display received coins and transfer history"""
    try:
        wallet = request.user.coin_wallet
    except SAFACoinWallet.DoesNotExist:
        messages.error(request, "You don't have a coin wallet yet.")
        return redirect('digital_coins:wallet')
    
    # Get received transfers
    received_transfers = SAFACoinTransfer.objects.filter(
        to_wallet=wallet
    ).select_related('from_wallet__user').order_by('-created_at')
    
    # Get sent transfers
    sent_transfers = SAFACoinTransfer.objects.filter(
        from_wallet=wallet
    ).select_related('to_wallet__user').order_by('-created_at')
    
    context = {
        'wallet': wallet,
        'received_transfers': received_transfers,
        'sent_transfers': sent_transfers,
    }
    
    return render(request, 'digital_coins/receive_coins.html', context)

# ============================================================================
# REWARDS SYSTEM
# ============================================================================

@login_required
def claim_reward(request, reward_id):
    """Claim a specific reward"""
    reward = get_object_or_404(SAFACoinReward, id=reward_id, user=request.user)
    
    if reward.claim_reward():
        messages.success(request, f"Successfully claimed {reward.amount} SAFA Coins!")
    else:
        messages.error(request, "Unable to claim reward. It may have expired or already been claimed.")
    
    return redirect('digital_coins:wallet')

@login_required
def claim_all_rewards(request):
    """Claim all available rewards"""
    pending_rewards = SAFACoinReward.objects.filter(
        user=request.user,
        claimed=False
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
    )
    
    claimed_count = 0
    total_coins = Decimal('0.0')
    
    for reward in pending_rewards:
        if reward.claim_reward():
            claimed_count += 1
            total_coins += reward.amount
    
    if claimed_count > 0:
        messages.success(request, f"Claimed {claimed_count} rewards for {total_coins} SAFA Coins!")
    else:
        messages.info(request, "No rewards available to claim.")
    
    return redirect('digital_coins:wallet')

# ============================================================================
# LOYALTY CONVERSION
# ============================================================================

@login_required
def loyalty_conversion(request):
    """Convert loyalty points to SAFA Coins"""
    if request.method == 'POST':
        points_to_convert = request.POST.get('points_to_convert')
        
        try:
            points_to_convert = int(points_to_convert)
            if points_to_convert <= 0:
                raise ValueError("Points must be positive")
        except (ValueError, TypeError):
            messages.error(request, "Please enter a valid number of points.")
            return redirect('digital_coins:loyalty_conversion')
        
        # Get user's loyalty points (this would integrate with your existing loyalty system)
        # For now, we'll use a placeholder
        user_loyalty_points = getattr(request.user, 'loyalty_points', 0) or 0
        
        if points_to_convert > user_loyalty_points:
            messages.error(request, f"You only have {user_loyalty_points} loyalty points available.")
            return redirect('digital_coins:loyalty_conversion')
        
        # Convert points to coins
        conversion = SAFACoinLoyaltyConversion.convert_loyalty_to_coins(
            request.user, points_to_convert
        )
        
        if conversion:
            messages.success(
                request, 
                f"Successfully converted {points_to_convert} loyalty points to {conversion.coins_awarded} SAFA Coins!"
            )
        else:
            messages.error(request, "Conversion failed. Please try again.")
        
        return redirect('digital_coins:wallet')
    
    # Get user's current loyalty points
    user_loyalty_points = getattr(request.user, 'loyalty_points', 0) or 0
    
    # Get conversion rate
    conversion_rate = Decimal('10.0')  # 10 points = 1 coin
    
    # Get conversion history
    conversion_history = SAFACoinLoyaltyConversion.objects.filter(
        user=request.user
    ).order_by('-converted_at')[:10]
    
    context = {
        'user_loyalty_points': user_loyalty_points,
        'conversion_rate': conversion_rate,
        'conversion_history': conversion_history,
    }
    
    return render(request, 'digital_coins/loyalty_conversion.html', context)

# ============================================================================
# GAMING COMPETITIONS
# ============================================================================

@login_required
def competitions_list(request):
    """Display all available competitions"""
    competitions = SAFACoinCompetition.objects.all().order_by('-start_date')
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        competitions = competitions.filter(status=status_filter)
    
    entry_fee_filter = request.GET.get('entry_fee')
    if entry_fee_filter == 'free':
        competitions = competitions.filter(entry_fee=0)
    elif entry_fee_filter == 'paid':
        competitions = competitions.filter(entry_fee__gt=0)
    
    # Get user's participations
    user_participations = SAFACoinCompetitionParticipation.objects.filter(
        user=request.user
    ).values_list('competition_id', flat=True)
    
    # Pagination
    paginator = Paginator(competitions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'competitions': page_obj,
        'page_obj': page_obj,
        'user_participations': user_participations,
        'is_paginated': page_obj.has_other_pages(),
    }
    
    return render(request, 'digital_coins/competitions.html', context)

@login_required
def competition_detail(request, competition_id):
    """Display competition details and allow joining"""
    competition = get_object_or_404(SAFACoinCompetition, id=competition_id)
    
    # Check if user is already participating
    try:
        participation = SAFACoinCompetitionParticipation.objects.get(
            competition=competition,
            user=request.user
        )
        user_participating = True
    except SAFACoinCompetitionParticipation.DoesNotExist:
        participation = None
        user_participating = False
    
    # Get participants
    participants = SAFACoinCompetitionParticipation.objects.filter(
        competition=competition
    ).select_related('user').order_by('-score', 'joined_at')
    
    context = {
        'competition': competition,
        'participation': participation,
        'user_participating': user_participating,
        'participants': participants,
        'can_join': competition.can_join(request.user) if not user_participating else False,
    }
    
    return render(request, 'digital_coins/competition_detail.html', context)

@login_required
@require_POST
def join_competition(request, competition_id):
    """Join a competition"""
    competition = get_object_or_404(SAFACoinCompetition, id=competition_id)
    
    if competition.join_competition(request.user):
        messages.success(request, f"Successfully joined {competition.name}!")
    else:
        messages.error(request, "Unable to join competition. Please check your coin balance and try again.")
    
    return redirect('digital_coins:competition_detail', competition_id=competition_id)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@login_required
def api_wallet_balance(request):
    """API endpoint to get wallet balance"""
    try:
        wallet = request.user.coin_wallet
        return JsonResponse({
            'balance': float(wallet.balance),
            'total_earned': float(wallet.total_earned),
            'total_spent': float(wallet.total_spent),
        })
    except SAFACoinWallet.DoesNotExist:
        return JsonResponse({'error': 'Wallet not found'}, status=404)

@login_required
def api_recent_transactions(request):
    """API endpoint to get recent transactions"""
    try:
        wallet = request.user.coin_wallet
        transactions = SAFACoinTransaction.objects.filter(
            wallet=wallet
        ).order_by('-created')[:10]
        
        transaction_data = []
        for transaction in transactions:
            transaction_data.append({
                'type': transaction.transaction_type,
                'amount': float(transaction.amount),
                'reason': transaction.reason,
                'created_at': transaction.created.isoformat(),
                'is_positive': transaction.transaction_type in ['EARNED', 'REWARD'],
            })
        
        return JsonResponse({'transactions': transaction_data})
    except SAFACoinWallet.DoesNotExist:
        return JsonResponse({'error': 'Wallet not found'}, status=404)

@login_required
def api_search_users(request):
    """API endpoint to search for users to send coins to"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'users': []})
    
    # Search users by name, email, or SAFA ID
    users = User.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query) |
        Q(safa_id__icontains=query)
    ).exclude(id=request.user.id)[:10]  # Exclude current user and limit results
    
    user_data = []
    for user in users:
        user_data.append({
            'id': user.id,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'full_name': user.get_full_name(),
            'email': user.email,
            'safa_id': user.safa_id,
        })
    
    return JsonResponse({'users': user_data})

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_or_create_wallet(user):
    """Get or create a wallet for a user"""
    wallet, created = SAFACoinWallet.objects.get_or_create(user=user)
    
    if created:
        # Give welcome bonus
        wallet.add_coins(Decimal('100.0'), "Welcome bonus - New SAFA member")
    
    return wallet

def award_daily_login_coins(user):
    """Award daily login coins to user"""
    today = timezone.now().date()
    
    # Check if already awarded today
    existing_reward = SAFACoinReward.objects.filter(
        user=user,
        reward_type='DAILY_LOGIN',
        created_at__date=today
    ).first()
    
    if not existing_reward:
        # Create daily login reward
        SAFACoinReward.objects.create(
            user=user,
            reward_type='DAILY_LOGIN',
            amount=Decimal('5.0'),
            reason="Daily login bonus"
        )
        return True
    
    return False

def award_match_participation_coins(user, match_id, match_name):
    """Award coins for match participation"""
    # Check if already awarded for this match
    existing_reward = SAFACoinReward.objects.filter(
        user=user,
        reward_type='MATCH_PARTICIPATION',
        metadata__match_id=match_id
    ).first()
    
    if not existing_reward:
        # Create match participation reward
        SAFACoinReward.objects.create(
            user=user,
            reward_type='MATCH_PARTICIPATION',
            amount=Decimal('10.0'),
            reason=f"Match participation: {match_name}",
            metadata={'match_id': match_id}
        )
        return True
    
    return False
