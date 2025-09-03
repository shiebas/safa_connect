from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()

class SAFACoinWallet(models.Model):
    """SAFA Coin wallet for each user"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='coin_wallet')
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=0, validators=[MinValueValidator(0)])
    total_earned = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    total_spent = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "SAFA Coin Wallet"
        verbose_name_plural = "SAFA Coin Wallets"
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.balance} SAFA Coins"
    
    def can_afford(self, amount):
        """Check if user can afford a transaction"""
        return self.balance >= amount
    
    def add_coins(self, amount, reason="Earned"):
        """Add coins to wallet"""
        if amount > 0:
            self.balance += amount
            self.total_earned += amount
            self.save()
            
            # Create transaction record
            SAFACoinTransaction.objects.create(
                wallet=self,
                transaction_type='EARNED',
                amount=amount,
                reason=reason,
                balance_after=self.balance
            )
            return True
        return False
    
    def spend_coins(self, amount, reason="Spent"):
        """Spend coins from wallet"""
        if self.can_afford(amount) and amount > 0:
            self.balance -= amount
            self.total_spent += amount
            self.save()
            
            # Create transaction record
            SAFACoinTransaction.objects.create(
                wallet=self,
                transaction_type='SPENT',
                amount=amount,
                reason=reason,
                balance_after=self.balance
            )
            return True
        return False

class SAFACoinTransaction(models.Model):
    """Record of all SAFA Coin transactions"""
    TRANSACTION_TYPES = [
        ('EARNED', 'Earned'),
        ('SPENT', 'Spent'),
        ('TRANSFER_SENT', 'Transfer Sent'),
        ('TRANSFER_RECEIVED', 'Transfer Received'),
        ('REFUND', 'Refund'),
        ('BONUS', 'Bonus'),
        ('LOYALTY_CONVERSION', 'Loyalty Conversion'),
        ('GAMING_REWARD', 'Gaming Reward'),
        ('GAMING_ENTRY', 'Gaming Entry Fee'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(SAFACoinWallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    reason = models.CharField(max_length=200)
    balance_after = models.DecimalField(max_digits=20, decimal_places=8)
    related_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='related_coin_transactions')
    metadata = models.JSONField(default=dict, blank=True)  # Store additional data like match_id, competition_id, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "SAFA Coin Transaction"
        verbose_name_plural = "SAFA Coin Transactions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.wallet.user.get_full_name()} - {self.transaction_type} {self.amount} coins"
    
    @property
    def is_positive(self):
        """Check if transaction adds coins to wallet"""
        return self.transaction_type in ['EARNED', 'TRANSFER_RECEIVED', 'REFUND', 'BONUS', 'LOYALTY_CONVERSION', 'GAMING_REWARD']

class SAFACoinTransfer(models.Model):
    """Record of coin transfers between users"""
    TRANSFER_STATUS = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_wallet = models.ForeignKey(SAFACoinWallet, on_delete=models.CASCADE, related_name='sent_transfers')
    to_wallet = models.ForeignKey(SAFACoinWallet, on_delete=models.CASCADE, related_name='received_transfers')
    amount = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(Decimal('0.00000001'))])
    status = models.CharField(max_length=20, choices=TRANSFER_STATUS, default='PENDING')
    message = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "SAFA Coin Transfer"
        verbose_name_plural = "SAFA Coin Transfers"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.from_wallet.user.get_full_name()} → {self.to_wallet.user.get_full_name()}: {self.amount} coins"
    
    def execute_transfer(self):
        """Execute the coin transfer"""
        if self.status == 'PENDING':
            if self.from_wallet.can_afford(self.amount):
                # Deduct from sender
                self.from_wallet.spend_coins(self.amount, f"Transfer to {self.to_wallet.user.get_full_name()}")
                
                # Add to receiver
                self.to_wallet.add_coins(self.amount, f"Transfer from {self.from_wallet.user.get_full_name()}")
                
                # Update transfer status
                self.status = 'COMPLETED'
                self.completed_at = timezone.now()
                self.save()
                
                return True
            else:
                self.status = 'FAILED'
                self.save()
                return False
        return False

class SAFACoinReward(models.Model):
    """System for earning coins through various activities"""
    REWARD_TYPES = [
        ('DAILY_LOGIN', 'Daily Login'),
        ('MATCH_PARTICIPATION', 'Match Participation'),
        ('LOYALTY_CONVERSION', 'Loyalty Points Conversion'),
        ('REFERRAL', 'Referral Bonus'),
        ('ACHIEVEMENT', 'Achievement Unlocked'),
        ('SOCIAL_ENGAGEMENT', 'Social Engagement'),
        ('GAMING_PARTICIPATION', 'Gaming Participation'),
        ('SEASON_COMPLETION', 'Season Completion'),
        ('TOURNAMENT_WIN', 'Tournament Win'),
        ('SPECIAL_EVENT', 'Special Event'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coin_rewards')
    reward_type = models.CharField(max_length=20, choices=REWARD_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(Decimal('0.00000001'))])
    reason = models.CharField(max_length=200)
    metadata = models.JSONField(default=dict, blank=True)  # Store additional context
    claimed = models.BooleanField(default=False)
    claimed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "SAFA Coin Reward"
        verbose_name_plural = "SAFA Coin Rewards"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.reward_type}: {self.amount} coins"
    
    def claim_reward(self):
        """Claim the reward and add coins to wallet"""
        if not self.claimed and (not self.expires_at or timezone.now() < self.expires_at):
            wallet, created = SAFACoinWallet.objects.get_or_create(user=self.user)
            if wallet.add_coins(self.amount, f"Reward: {self.reason}"):
                self.claimed = True
                self.claimed_at = timezone.now()
                self.save()
                return True
        return False
    
    @property
    def is_expired(self):
        """Check if reward has expired"""
        return self.expires_at and timezone.now() > self.expires_at
    
    @property
    def can_claim(self):
        """Check if reward can be claimed"""
        return not self.claimed and not self.is_expired

class SAFACoinCompetition(models.Model):
    """Gaming competitions that use SAFA Coins"""
    COMPETITION_TYPES = [
        ('FANTASY_FOOTBALL', 'Fantasy Football'),
        ('PREDICTION_GAME', 'Prediction Game'),
        ('SKILL_CHALLENGE', 'Skill Challenge'),
        ('TRIVIA', 'Football Trivia'),
        ('TOURNAMENT', 'Tournament'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    competition_type = models.CharField(max_length=20, choices=COMPETITION_TYPES)
    entry_fee = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0)])
    prize_pool = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0)])
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    current_participants = models.PositiveIntegerField(default=0)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    rules = models.JSONField(default=dict, blank=True)
    prize_distribution = models.JSONField(default=dict, blank=True)  # e.g., {"1": 0.5, "2": 0.3, "3": 0.2}
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_competitions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "SAFA Coin Competition"
        verbose_name_plural = "SAFA Coin Competitions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_competition_type_display()}"
    
    @property
    def is_active(self):
        """Check if competition is currently active"""
        now = timezone.now()
        return self.status == 'ACTIVE' and self.start_date <= now <= self.end_date
    
    @property
    def is_full(self):
        """Check if competition is full"""
        return self.max_participants and self.current_participants >= self.max_participants
    
    def can_join(self, user):
        """Check if user can join competition"""
        if not self.is_active or self.is_full:
            return False
        
        # Check if user has enough coins
        try:
            wallet = user.coin_wallet
            return wallet.can_afford(self.entry_fee)
        except SAFACoinWallet.DoesNotExist:
            return False
    
    def join_competition(self, user):
        """Add user to competition"""
        if self.can_join(user):
            wallet = user.coin_wallet
            if wallet.spend_coins(self.entry_fee, f"Entry fee for {self.name}"):
                self.current_participants += 1
                self.save()
                
                # Create participation record
                SAFACoinCompetitionParticipation.objects.create(
                    competition=self,
                    user=user,
                    entry_fee_paid=self.entry_fee
                )
                return True
        return False

class SAFACoinCompetitionParticipation(models.Model):
    """Track user participation in competitions"""
    competition = models.ForeignKey(SAFACoinCompetition, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='competition_participations')
    entry_fee_paid = models.DecimalField(max_digits=20, decimal_places=8)
    score = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rank = models.PositiveIntegerField(null=True, blank=True)
    prizes_won = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    joined_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "SAFA Coin Competition Participation"
        verbose_name_plural = "SAFA Coin Competition Participations"
        unique_together = ['competition', 'user']
        ordering = ['-score', 'joined_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} in {self.competition.name}"
    
    def award_prize(self, prize_amount):
        """Award prize coins to participant"""
        if prize_amount > 0:
            wallet = self.user.coin_wallet
            if wallet.add_coins(prize_amount, f"Prize from {self.competition.name}"):
                self.prizes_won += prize_amount
                self.save()
                return True
        return False

class SAFACoinLoyaltyConversion(models.Model):
    """Convert loyalty points to SAFA Coins"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loyalty_conversions')
    loyalty_points = models.PositiveIntegerField()
    coins_awarded = models.DecimalField(max_digits=20, decimal_places=8)
    conversion_rate = models.DecimalField(max_digits=10, decimal_places=4)  # points per coin
    converted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "SAFA Coin Loyalty Conversion"
        verbose_name_plural = "SAFA Coin Loyalty Conversions"
        ordering = ['-converted_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()}: {self.loyalty_points} points → {self.coins_awarded} coins"
    
    @classmethod
    def convert_loyalty_to_coins(cls, user, points_to_convert):
        """Convert loyalty points to coins"""
        # Get current conversion rate (configurable)
        conversion_rate = Decimal('10.0')  # 10 loyalty points = 1 coin
        
        if points_to_convert >= conversion_rate:
            coins_awarded = points_to_convert / conversion_rate
            
            # Create conversion record
            conversion = cls.objects.create(
                user=user,
                loyalty_points=points_to_convert,
                coins_awarded=coins_awarded,
                conversion_rate=conversion_rate
            )
            
            # Award coins to user
            wallet, created = SAFACoinWallet.objects.get_or_create(user=user)
            wallet.add_coins(coins_awarded, f"Loyalty conversion: {points_to_convert} points")
            
            return conversion
        return None
