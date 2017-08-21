from __future__ import unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url('^advertisements/banners/$', views.BannersView.as_view(), name='banners'),
    url('^advertisements/banners2/$', views.Banners2View.as_view(), name='banners2'),
]
