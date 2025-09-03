from django.apps import AppConfig


class DigitalCoinsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'digital_coins'
    verbose_name = 'SAFA Digital Coins'
    
    def ready(self):
        """Import signals when app is ready"""
        try:
            import digital_coins.signals
        except ImportError:
            pass
