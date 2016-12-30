from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('articles/editor', views.ArticleViewSet)
router.register('articles', views.PublicArticleViewSet)

urlpatterns = [
    url(r'^articles/content/$', views.ArticleContentViewSet.as_view({
        'post': 'create'
    })),
    url(r'^articles/content/(?P<pk>\d+)/$', views.ArticleContentViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
    url(r'', include(router.urls))
]


