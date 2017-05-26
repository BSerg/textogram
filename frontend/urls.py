from django.conf.urls import url

from frontend.views import ArticleView, EditorView
from textogram.settings import IS_LENTACH
from .views import BaseTemplateView

urlpatterns = [
    url(r'articles/new/?$', BaseTemplateView.as_view(template_name='index.html'), name='article_new'),
    url(r'articles/(?P<slug>[\-\w]+)(/gallery/[\w\-]+)?/?$', ArticleView.as_view(), name='article'),
    url(r'articles/(?P<pk>[\-\w]+)/edit?$', EditorView.as_view(), name='editor'),
]

if IS_LENTACH:
    urlpatterns += [url(r'^(login|articles/[\-\w]+/edit|articles/(?P<id>\d+)/preview|id\d+|id\d+/\w+|drafts|manage|manage/\w+|feed|auth/twitter|url_shorten)?/?$',
        BaseTemplateView.as_view(template_name='index.html'))]

else:
    urlpatterns += [url(r'^(login|articles/[\-\w]+/edit|articles/(?P<id>\d+)/preview|[^!][\w]+|[^!][\w]+/\w+|drafts|manage|manage/\w+|feed|auth/twitter|url_shorten)?/?$',
        BaseTemplateView.as_view(template_name='index.html'))]
