from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import logging

from .models import DigitalCard, PhysicalCard

User = get_user_model()
logger = logging.getLogger(__name__)

def get_membership_expiry_date(user):
    """Safely get the membership expiry date from the user's member profile and season."""
    if hasattr(user, 'member_profile') and user.member_profile and user.member_profile.current_season:
        return user.member_profile.current_season.season_end_date
    # Default fallback: one year from now
    return timezone.now().date() + timedelta(days=365)

@receiver(pre_save, sender=User)
def capture_previous_membership_status(sender, instance, **kwargs):
    """Capture the previous membership status before saving"""
    if instance.pk:
        try:
            instance._previous_membership_status = User.objects.get(pk=instance.pk).membership_status
        except User.DoesNotExist:
            instance._previous_membership_status = None
    else:
        instance._previous_membership_status = None

@receiver(post_save, sender=User)
def handle_membership_activation(sender, instance, created, **kwargs):
    """
    Automatically generate cards when membership is activated
    Triggered when membership status changes from PAID → ACTIVE
    """
    
    # Only process if user has a SAFA ID (security requirement)
    if not instance.safa_id:
        return
    
    # Check if membership status changed to ACTIVE
    previous_status = getattr(instance, '_previous_membership_status', None)
    current_status = instance.membership_status
    
    if current_status == 'ACTIVE' and previous_status in ['PAID', 'PENDING']:
        logger.info(f"Membership activated for user {instance.email}. Generating cards...")
        
        expiry_date = get_membership_expiry_date(instance)

        # Generate Digital Card (always created for active members)
        digital_card, created = DigitalCard.objects.get_or_create(
            user=instance,
            defaults={
                'expires_date': expiry_date,
                'status': 'ACTIVE'
            }
        )
        
        if created:
            logger.info(f"Digital card #{digital_card.card_number} created for {instance.email}")
        else:
            # Update existing card
            digital_card.status = 'ACTIVE'
            digital_card.expires_date = expiry_date
            digital_card.save()
            logger.info(f"Digital card #{digital_card.card_number} updated for {instance.email}")
        
        # Generate Physical Card (only if requested)
        if hasattr(instance, 'member_profile') and (instance.member_profile.physical_card_requested or instance.member_profile.card_delivery_preference in ['PHYSICAL_ONLY', 'BOTH']):
            physical_card, created = PhysicalCard.objects.get_or_create(
                user=instance,
                defaults={
                    'card_number': digital_card.card_number,
                    'shipping_address': instance.member_profile.physical_card_delivery_address or '',
                    'print_status': 'PENDING'
                }
            )
            
            if created:
                logger.info(f"Physical card #{physical_card.card_number} ordered for {instance.email}")
            else:
                logger.info(f"Physical card #{physical_card.card_number} already exists for {instance.email}")

@receiver(post_save, sender=User)
def handle_membership_suspension(sender, instance, **kwargs):
    """
    Suspend cards when membership is suspended or expired
    """
    if instance.membership_status in ['SUSPENDED', 'EXPIRED']:
        
        # Suspend digital card
        try:
            digital_card = instance.digital_card
            digital_card.status = 'SUSPENDED' if instance.membership_status == 'SUSPENDED' else 'EXPIRED'
            digital_card.save()
            logger.info(f"Digital card #{digital_card.card_number} suspended for {instance.email}")
        except DigitalCard.DoesNotExist:
            pass
        
        # Note: Physical cards don't need status changes since they're physical objects
        # But we could track this in the PhysicalCard model if needed

@receiver(post_save, sender=User)
def update_card_expiry_dates(sender, instance, **kwargs):
    """
    Update card expiry dates when membership expiry date changes
    """
    expiry_date = get_membership_expiry_date(instance)
    if expiry_date:
        try:
            digital_card = instance.digital_card
            if digital_card.expires_date != expiry_date:
                digital_card.expires_date = expiry_date
                digital_card.save()
                logger.info(f"Updated expiry date for digital card #{digital_card.card_number}")
        except DigitalCard.DoesNotExist:
            pass
