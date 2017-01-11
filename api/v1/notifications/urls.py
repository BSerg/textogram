from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from api.v1.notifications import views

router = DefaultRouter()

router.register('notifications', views.NotificationViewSet)

urlpatterns = [
    url(r'', include(router.urls))
]
