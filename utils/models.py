from django.db import models
from django.utils.html import format_html
from django_extensions.db.models import TimeStampedModel

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
        return format_html('<span>No logo</span>')
    
    display_logo.short_description = 'Logo'