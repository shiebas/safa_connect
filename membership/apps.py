from django.apps import AppConfig


class MembershipConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "membership"
    verbose_name = 'SAFA Membership & Invoicing'

def ready(self):
        """
        Import signals when the app is ready
        This ensures all signal handlers are connected
        """
        try:
            import membership.signals
            print("✅ SAFA Membership signals loaded successfully")
        except ImportError as e:
            print(f"❌ Failed to load membership signals: {e}")
        
        # Import any other startup code
        try:
            from .safa_invoice_manager import SAFAInvoiceManager
            print("✅ SAFA Invoice Manager loaded successfully")
        except ImportError as e:
            print(f"❌ Failed to load SAFA Invoice Manager: {e}")