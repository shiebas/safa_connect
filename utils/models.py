from django.db import models
from django.utils.html import format_html
from django.templatetags.static import static
import random
import string

class ModelWithLogo(models.Model):
    """
    Abstract base class for models that have a logo.
    Provides a logo field and helper methods for display.
    """
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    
    class Meta:
        abstract = True
    
    def display_logo(self):
        """Returns an HTML img tag to display the logo in the admin"""
        if self.logo:
            return format_html('<img src="{}" width="50" height="50" />', self.logo.url)
        # Display default logo from static files
        default_logo_url = static('images/default_logo.png')  # Fix: remove 'static/' prefix
        return format_html('<img src="{}" width="50" height="50" alt="Default Logo" />', default_logo_url)
    
    display_logo.short_description = 'Logo'


class SAFAIdentifiableMixin(models.Model):
    """Mixin that adds a SAFA ID field to any model"""
    safa_id = models.CharField(
        'SAFA ID', 
        max_length=5, 
        unique=True, 
        blank=True,
        help_text="Unique 5-character SAFA identifier"
    )
    
    class Meta:
        abstract = True
    
    @staticmethod
    def generate_unique_safa_id():
        """Generate a random 5-character alphanumeric SAFA ID that is unique across all models"""
        from django.apps import apps
        
        # Get all models that use SAFAIdentifiableMixin
        safa_models = []
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                if issubclass(model, SAFAIdentifiableMixin) and model._meta.abstract is False:
                    safa_models.append(model)
        
        # Character set for the ID
        chars = string.ascii_uppercase + string.digits
        
        # Try up to 100 times to generate a unique ID
        for _ in range(100):
            # Generate a random 5-character string
            safa_id = ''.join(random.choice(chars) for _ in range(5))
            
            # Check if this ID already exists in any model that uses the mixin
            exists = False
            for model in safa_models:
                if model.objects.filter(safa_id=safa_id).exists():
                    exists = True
                    break
            
            if not exists:
                return safa_id
        
        raise ValueError("Could not generate a unique SAFA ID after multiple attempts")
    
    def save(self, *args, **kwargs):
        # Generate SAFA ID if not already set
        if not self.safa_id:
            self.safa_id = self.generate_unique_safa_id()
        super().save(*args, **kwargs)