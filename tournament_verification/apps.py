from django.apps import AppConfig

class TournamentVerificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tournament_verification'
    verbose_name = 'Tournament Verification System'
    
    def ready(self):
        import tournament_verification.signals

