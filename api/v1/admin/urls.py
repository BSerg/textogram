from __future__ import unicode_literals
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register('admin/articles', views.AdminArticleViewSet)
router.register('admin/authors', views.AdminUserViewSet)

urlpatterns = [
    url(r'', include(router.urls))
]
