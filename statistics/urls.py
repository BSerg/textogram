from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^access_token/yandex/$', views.YandexAuthorization.as_view()),
    url(r'^access_token/yandex/callback/$', views.YandexAuthorizationCallback.as_view()),
]
