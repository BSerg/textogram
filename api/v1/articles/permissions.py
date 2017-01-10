from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS

from articles.models import Article


class IsOwnerForUnsafeRequests(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsArticleContentOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST':
            article_id = request.data.get('article')
            try:
                Article.objects.get(pk=article_id, owner=request.user)
            except Article.DoesNotExist:
                return False
            else:
                return True
        return True

    def has_object_permission(self, request, view, obj):
        return obj.article.owner == request.user


class IsArticleContentPhotoOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.content_item.article.owner == request.user
