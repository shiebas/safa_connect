from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Template filter to lookup dictionary values by key"""
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    if hasattr(dictionary, '__getitem__'):
        try:
            return dictionary[key]
        except (KeyError, TypeError):
            return None
    return getattr(dictionary, key, None)

@register.filter
def class_name(obj):
    """Get the class name of an object"""
    return obj.__class__.__name__
