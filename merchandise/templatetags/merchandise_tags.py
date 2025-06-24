from django import template
from django.utils.safestring import mark_safe
from django.utils import timezone
from datetime import timedelta
import hashlib

register = template.Library()

@register.filter
def placeholder_image(product_or_name, size="400x300"):
    """Generate a placeholder image URL for products"""
    # Handle both Product objects and strings
    if hasattr(product_or_name, 'name'):
        # It's a Product object
        product_name = product_or_name.name
    else:
        # It's a string
        product_name = str(product_or_name)
    
    # Create a deterministic color based on product name
    hash_object = hashlib.md5(product_name.encode())
    hex_dig = hash_object.hexdigest()
    
    # Extract RGB values from hash
    r = int(hex_dig[0:2], 16)
    g = int(hex_dig[2:4], 16) 
    b = int(hex_dig[4:6], 16)
    
    # Create a placeholder URL
    color = f"{r:02x}{g:02x}{b:02x}"
    url = f"https://via.placeholder.com/{size}/{color}/ffffff?text={product_name.replace(' ', '+')}"
    
    return url

@register.filter
def product_image_or_placeholder(product, size="400x300"):
    """Return product main image URL or placeholder"""
    if hasattr(product, 'main_image') and product.main_image:
        return product.main_image.url
    return placeholder_image(product.name, size)

@register.filter
def lookup(dictionary, key):
    """Template filter to lookup dictionary values"""
    return dictionary.get(key, 0)

@register.filter
def is_new_product(product, days=30):
    """Check if product was created within the last X days"""
    if not hasattr(product, 'created_at'):
        return False
    cutoff_date = timezone.now() - timedelta(days=days)
    return product.created_at >= cutoff_date
