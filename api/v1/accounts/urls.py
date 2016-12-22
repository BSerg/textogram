from __future__ import unicode_literals
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('users', views.PublicUserViewSet)

urlpatterns = [
    url(r'users/me/$', views.UserViewSet.as_view({'get': 'me'})),
    url(r'', include(router.urls))
]

