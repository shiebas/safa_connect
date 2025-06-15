from rest_framework import permissions
from .models import SupporterProfile

class IsSupporterSelfOrReadOnly(permissions.BasePermission):
    """
    Supporters can view and edit their own profile. Others can only view.
    """
    def has_object_permission(self, request, view, obj):
        # Allow read for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        # Only allow edit if the user owns the profile
        return obj.user == request.user
