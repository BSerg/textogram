from rest_framework import permissions


class CustomAdminPermission(permissions.AllowAny):
    def has_permission(self, request, view):
        hp = super(CustomAdminPermission, self).has_permission(request, view)
        print request.META
        print request.user
        print hp
        return True


class CustomAdminPermissionAlt(permissions.BasePermission):

    def has_permission(self, request, view):
        if not request.method == 'OPTIONS':
            print request.method
            print 'TUTACHKI'
        # print request.method
        # print request.user
        # print request.META
        return True
