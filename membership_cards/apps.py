from django.apps import AppConfig

class MembershipCardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'membership_cards'
    
    def ready(self):
        import membership_cards.signals  # Import signals when app is ready
