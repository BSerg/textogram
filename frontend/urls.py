from django.conf.urls import url, include
from django.views.generic.base import TemplateView
from .views import BaseTemplateView

from frontend.views import ArticleView

urlpatterns = [
    url(r'articles/new/?$', BaseTemplateView.as_view(template_name='index.html'), name='article_new'),
    url(r'articles/(?P<slug>[\-\w]+)/?$', ArticleView.as_view(), name='article'),
    url(r'^(login|articles/[\-\w]+/edit||articles/(?P<id>\d+)/preview|id\d+|id\d+/\w+|profile/\w+|drafts|manage|feed|auth/twitter|url_shorten)?/?$',
        BaseTemplateView.as_view(template_name='index.html')),
]
