from __future__ import unicode_literals

from django.conf.urls import url

from api.v1.payments import views

urlpatterns = [
    url(r'^payments/form/$', views.YandexKassaFormView.as_view()),
]
