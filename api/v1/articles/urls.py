from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('articles/editor/images', views.ArticleImageViewSet)
router.register('articles/editor', views.ArticleViewSet)
router.register('drafts', views.DraftListViewSet)

urlpatterns = [
    url(r'', include(router.urls)),
    url('^articles/$', views.PublicArticleListViewSet.as_view({'get': 'list'}), name='articles_list'),
    url('^articles/(?P<slug>[\w]+)/$', views.PublicArticleListViewSet.as_view({'get': 'retrieve'}), name='article'),
]
