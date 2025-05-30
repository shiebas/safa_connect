from django.contrib import admin
from django.utils.html import format_html

class ModelWithLogoAdmin(admin.ModelAdmin):
    """Base admin class for models with logo functionality"""
    
    list_display = ['__str__', 'display_logo']

    def display_logo(self, obj):
        """
        Display the logo as an HTML img tag
        Args:
            obj: The model instance
        Returns:
            SafeString: HTML img tag with logo
        """
        if hasattr(obj, 'logo_url'):
            return format_html('<img src="{}" width="50" height="50" />', obj.logo_url)
        return '-'

    display_logo.short_description = 'Logo'
    display_logo.allow_tags = True