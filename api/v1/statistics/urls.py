from __future__ import unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^statistics/(?P<nickname>[\w\-]+)/common/$', views.UserCommonStatisticsView.as_view({'get': 'retrieve'})),
    url(r'^statistics/articles/$', views.ArticleCommonStatisticsListView.as_view({'get': 'list'})),
    url(r'^statistics/articles/(?P<pk>\d+)/$', views.ArticleStatisticsView.as_view({'get': 'retrieve'})),
]
