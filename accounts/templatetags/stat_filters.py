from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter(name='percentage')
def percentage(value, total):
    """Calculate percentage safely"""
    try:
        if int(total) > 0:
            return floatformat((float(value) / float(total)) * 100, 0)
        return "0"
    except (ValueError, ZeroDivisionError, TypeError):
        return "0"

@register.filter(name='subtract')
def subtract(value, arg):
    """Subtract the arg from the value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='remainder')
def remainder(value):
    """Calculate the remainder to 100%"""
    try:
        value = int(float(value))
        return 100 - value
    except (ValueError, TypeError):
        return 0
