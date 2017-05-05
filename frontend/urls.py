from django.conf.urls import url, include
from django.views.generic.base import TemplateView
from .views import BaseTemplateView
from textogram.settings import IS_LENTACH

from frontend.views import ArticleView

urlpatterns = [
    url(r'articles/new/?$', BaseTemplateView.as_view(template_name='index.html'), name='article_new'),
    url(r'articles/(?P<slug>[\-\w]+)/?$', ArticleView.as_view(), name='article'),
    #url(r'^(login|articles/[\-\w]+/edit|articles/(?P<id>\d+)/preview|id\d+|id\d+/\w+|drafts|manage|manage/\w+|feed|auth/twitter|url_shorten)?/?$',
    #    BaseTemplateView.as_view(template_name='index.html')),
]

# urlpatterns.append(url(r'^(login|articles/[\-\w]+/edit|articles/(?P<id>\d+)/preview|id\d+|id\d+/\w+|drafts|manage|manage/\w+|feed|auth/twitter|url_shorten)?/?$',
#         BaseTemplateView.as_view(template_name='index.html')) )

if IS_LENTACH:
    urlpatterns += [url(r'^(login|articles/[\-\w]+/edit|articles/(?P<id>\d+)/preview|id\d+|id\d+/\w+|drafts|manage|manage/\w+|feed|auth/twitter|url_shorten)?/?$',
        BaseTemplateView.as_view(template_name='index.html'))]

else:
    urlpatterns += [url(r'^(login|articles/[\-\w]+/edit|articles/(?P<id>\d+)/preview|[^!][\w]+|[^!][\w]+/\w+|drafts|manage|manage/\w+|feed|auth/twitter|url_shorten)?/?$',
        BaseTemplateView.as_view(template_name='index.html'))]
