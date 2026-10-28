
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """
    Allow all authenticated users to read.
    Only administrators can create, update, or delete records.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        return request.user.is_staff


class IsAdminOrOrderOwner(BasePermission):
    """
    Administrators can access any order.
    Standard users can access only their own orders.
    """

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        return obj.created_by_id == request.user.id
