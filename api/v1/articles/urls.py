from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('articles/editor/images', views.ArticleImageViewSet)
router.register('articles/editor', views.ArticleViewSet)
router.register('articles', views.PublicArticleViewSet)

urlpatterns = [
    url(r'', include(router.urls))
]
