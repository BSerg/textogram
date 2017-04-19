from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from api.v1.url_shortener import views

router = DefaultRouter()

router.register('url_short', views.UrlShortViewSet)

urlpatterns = [
    url(r'', include(router.urls))
]