from django import template

register = template.Library()

@register.filter(name='format_card_number')
def format_card_number(value):
    """Format a card number with spaces for better readability"""
    if not value:
        return ''
    value = str(value).strip()
    return ' '.join([value[i:i+4] for i in range(0, len(value), 4)])

@register.filter(name='mask_card')
def mask_card(value):
    """Mask a card number for security, showing only last 4 digits"""
    if not value:
        return ''
    value = str(value).strip()
    if len(value) <= 4:
        return value
    return '*' * (len(value) - 4) + value[-4:]

@register.filter(name='card_status_class')
def card_status_class(status):
    """Return a Bootstrap class based on card status"""
    status_classes = {
        'active': 'success',
        'pending': 'warning',
        'expired': 'danger',
        'suspended': 'secondary',
        'revoked': 'dark'
    }
    status = str(status).lower()
    return f"badge bg-{status_classes.get(status, 'info')}"
