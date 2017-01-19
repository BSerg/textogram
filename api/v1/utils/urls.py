from __future__ import unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^utils/embed/', views.EmbedAPIView.as_view()),
    url(r'^utils/vk/access_token/', views.VKAccessTokenView.as_view()),
]
