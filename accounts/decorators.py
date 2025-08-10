from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required

def role_required(allowed_roles=None, allow_superuser=True, allow_staff=False):
    """
    Decorator to check if user has required role
    
    Args:
        allowed_roles (list): List of allowed role strings
        allow_superuser (bool): Whether to allow superusers
        allow_staff (bool): Whether to allow staff users
    """
    if allowed_roles is None:
        allowed_roles = []
    
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            user = request.user
            
            # Allow superusers if specified
            if allow_superuser and user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Allow staff if specified
            if allow_staff and user.is_staff:
                return view_func(request, *args, **kwargs)
            
            # Check if user has required role
            if hasattr(user, 'role') and user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            # Deny access if none of the conditions are met
            raise PermissionDenied("You don't have permission to access this page.")
        
        return wrapped_view
    return decorator
