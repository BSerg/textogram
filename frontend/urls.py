from django.conf.urls import url, include
from django.views.generic.base import TemplateView

from frontend.views import ArticleView

urlpatterns = [
    url(r'articles/(?P<slug>[\-\w]+)/?$', ArticleView.as_view(), name='article'),
    url(r'^(articles/[\-\w]+/edit|profile/\w+|drafts|manage|auth/twitter)?/?$',
        TemplateView.as_view(template_name='index.html')),

]
