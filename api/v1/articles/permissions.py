from rest_framework import permissions

from articles.models import Article
from textogram.settings import DEBUG


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsOwnerForUnsafeRequests(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if DEBUG and obj.status == Article.SHARED:
            return True
        if request.method == 'POST':
            return True
        return obj.owner == request.user


class IsArticleContentOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST':
            article_id = request.data.get('article')
            try:
                article = Article.objects.get(pk=article_id)
            except Article.DoesNotExist:
                return False
            else:
                if DEBUG and article.status == Article.SHARED:
                    return True
                return article.owner == request.user
        return True

    def has_object_permission(self, request, view, obj):
        return obj.article.owner == request.user


class WebVisor(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated() and request.method not in permissions.SAFE_METHODS:
            return False
        return True


class IsArticleContentPhotoOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.content_item.article.owner == request.user
