from rest_framework import permissions

class IsClubAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission: Club admins can view and edit their own club's data.
    Others can only view.
    """
    def has_permission(self, request, view):
        # Allow read for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        # Only allow write for club admins
        return request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'CLUB_ADMIN'

    def has_object_permission(self, request, view, obj):
        # Allow read for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        # Only allow edit if user is club admin and owns the club
        return (
            getattr(request.user, 'role', None) == 'CLUB_ADMIN' and
            hasattr(request.user, 'club') and
            obj == request.user.club
        )

class IsLFAViewOnly(permissions.BasePermission):
    """
    LFA admins can view clubs in their LFA, but cannot edit/delete/add.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Only allow safe methods
        if request.method in permissions.SAFE_METHODS:
            return getattr(request.user, 'role', None) == 'ADMIN_LOCAL_FED' and hasattr(request.user, 'local_federation') and obj.localfootballassociation == request.user.local_federation
        return False

class IsRegionViewOnly(permissions.BasePermission):
    """
    Region admins can view clubs in their region, but cannot edit/delete/add.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return getattr(request.user, 'role', None) == 'ADMIN_REGION' and hasattr(request.user, 'region') and obj.region == request.user.region
        return False

class IsProvinceViewOnly(permissions.BasePermission):
    """
    Province admins can view clubs in their province, but cannot edit/delete/add.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return getattr(request.user, 'role', None) == 'ADMIN_PROVINCE' and hasattr(request.user, 'province') and obj.province == request.user.province
        return False

class IsNationalViewOnly(permissions.BasePermission):
    """
    National admins can view all clubs, but cannot edit/delete/add.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'ADMIN_NATIONAL'

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS
