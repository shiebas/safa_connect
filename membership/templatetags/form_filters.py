# This module requires Django and the django-widget-tweaks package to be installed
# To install django-widget-tweaks: pip install django-widget-tweaks
from django import template
from django.template.defaulttags import csrf_token as original_csrf_token

register = template.Library()

# Register the built-in csrf_token tag to help IDE recognize it
register.tag('csrf_token', original_csrf_token)

@register.filter(name='add_class')
def add_class(field, css_class):
    """Add CSS class to form field"""
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={'class': css_class})
    return field

@register.filter(name='attr')
def attr(field, attr_args):
    """Add attribute to form field"""
    attrs = {}

    # Split the attribute arguments by pipe (|)
    parts = attr_args.split('|')

    for part in parts:
        # Split each part by colon (:) to get key and value
        if ':' in part:
            key, value = part.split(':', 1)
            attrs[key] = value

    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs=attrs)
    return field
