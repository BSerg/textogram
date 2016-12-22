from django.conf.urls import url, include
from django.views.generic.base import TemplateView

urlpatterns = [
    url(r'^(articles/[\-\w]+|articles/[\-\w]+/edit|profile/\w+)?/?$', TemplateView.as_view(template_name='index.html'))
]
