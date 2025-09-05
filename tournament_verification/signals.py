from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TournamentRegistration
from .tournament_models import TournamentTeam
import threading

@receiver(post_save, sender=TournamentRegistration)
def generate_team_photo_on_registration(sender, instance, created, **kwargs):
    """Automatically generate team photo when a player registers"""
    if created and instance.team and instance.verification_status == 'VERIFIED':
        # Generate team photo in background to avoid blocking the request
        def generate_photo():
            try:
                instance.team.generate_team_photo()
            except Exception as e:
                print(f"Error generating team photo for {instance.team.name}: {e}")
        
        # Run in background thread
        thread = threading.Thread(target=generate_photo)
        thread.daemon = True
        thread.start()

@receiver(post_save, sender=TournamentRegistration)
def update_team_photo_on_verification(sender, instance, created, **kwargs):
    """Update team photo when a registration is verified"""
    if not created and instance.team and instance.verification_status == 'VERIFIED':
        # Check if this is a status change to VERIFIED
        if hasattr(instance, '_previous_verification_status'):
            if instance._previous_verification_status != 'VERIFIED':
                # Generate team photo in background
                def generate_photo():
                    try:
                        instance.team.generate_team_photo()
                    except Exception as e:
                        print(f"Error updating team photo for {instance.team.name}: {e}")
                
                thread = threading.Thread(target=generate_photo)
                thread.daemon = True
                thread.start()


