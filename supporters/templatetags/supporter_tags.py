from django import template

register = template.Library()

@register.filter
def lookup(form, field_name):
    """Template filter to lookup form field by name."""
    try:
        return form[field_name]
    except KeyError:
        return None

@register.filter
def class_name(obj):
    """Template filter to get class name of an object."""
    return obj.__class__.__name__
