from __future__ import unicode_literals

from rest_framework import permissions


class IsAdminOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method not in permissions.SAFE_METHODS:
            if not request.user.is_authenticated() or not request.user.is_superuser and obj != request.user:
                return False
        return True
