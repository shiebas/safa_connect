from django.contrib import messages
from django.shortcuts import redirect

def role_required(allowed_roles=None, allow_superuser=False, allow_staff=False):
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'You must be logged in to access this page.')
                return redirect('accounts:login') # Redirect to login if not authenticated

            if (allow_superuser and request.user.is_superuser) or \
               (allow_staff and request.user.is_staff) or \
               (hasattr(request.user, 'role') and request.user.role in allowed_roles):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('accounts:dashboard') # Or a more appropriate redirect
        return wrapper_func
    return decorator