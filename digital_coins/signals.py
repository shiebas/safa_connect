from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from .models import SAFACoinWallet, SAFACoinReward

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    """Automatically create a SAFA Coin wallet for new users"""
    if created:
        # Create wallet with welcome bonus
        wallet = SAFACoinWallet.objects.create(user=instance)
        wallet.add_coins(Decimal('100.0'), "Welcome bonus - New SAFA member")
        
        # Create first daily login reward
        SAFACoinReward.objects.create(
            user=instance,
            reward_type='DAILY_LOGIN',
            amount=Decimal('5.0'),
            reason="First daily login bonus"
        )

@receiver(post_save, sender=User)
def award_daily_login_coins(sender, instance, created, **kwargs):
    """Award daily login coins to existing users"""
    if not created:  # Only for existing users
        # Check if user has logged in today
        today = timezone.now().date()
        
        # Check if already awarded today
        existing_reward = SAFACoinReward.objects.filter(
            user=instance,
            reward_type='DAILY_LOGIN',
            created_at__date=today
        ).first()
        
        if not existing_reward:
            # Create daily login reward
            SAFACoinReward.objects.create(
                user=instance,
                reward_type='DAILY_LOGIN',
                amount=Decimal('5.0'),
                reason="Daily login bonus"
            )
