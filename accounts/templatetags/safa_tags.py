from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def replace(value, arg):
    """Replace old with new in string"""
    if len(arg.split(',')) != 2:
        return value
    old, new = arg.split(',')  # Split into two variables for parsing comma-separated values
    return value.replace(old, new)  # Replace the old and replace it with the new one

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary"""
    return dictionary.get(key)

@register.simple_tag
def membership_status_badge(status):
    """Render membership status badge"""
    badge_map = {
        'PENDING': 'warning',
        'ACTIVE': 'success',
        'SUSPENDED': 'danger',
        'EXPIRED': 'secondary'
    }
    
    badge_class = badge_map.get(status, 'secondary')
    return mark_safe(f'<span class="badge bg-{badge_class}">{status.title()}</span>')

@register.simple_tag
def role_badge(role):
    """Render role badge"""
    return mark_safe(f'<span class="badge bg-primary">{role.replace("_", " ").title()}</span>')

@register.filter
def format_currency(amount):
    """Format amount as South African Rand"""
    if amount is None:
        return 'R0.00'
    return f'R{amount:,.2f}'
