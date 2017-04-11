from django.conf.urls import url, include
from django.views.generic.base import TemplateView
from .views import BaseTemplateView

from frontend.views import ArticleView

urlpatterns = [
    url(r'articles/new/?$', BaseTemplateView.as_view(template_name='index.html'), name='article_new'),
    url(r'articles/(?P<slug>[\-\w]+)/?$', ArticleView.as_view(), name='article'),
    url(r'^(articles/[\-\w]+/edit|articles/(?P<id>\d+)/preview|profile/\w+|drafts|manage|auth/twitter)?/?$',
        BaseTemplateView.as_view(template_name='index.html')),

]
