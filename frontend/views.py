from django.shortcuts import render_to_response
from django.template import RequestContext
from django.urls import reverse
from django.views.generic import DetailView, TemplateView

from articles import ArticleContentType
from articles.models import Article
from textogram.settings import DEBUG
from rest_framework.authtoken.models import Token
from django.http.response import HttpResponseRedirect
from textogram.settings import IS_LENTACH


class BaseTemplateView(TemplateView):

    def get(self, request, *args, **kwargs):

        if request.path == '/' and request.COOKIES.get('authToken', ''):
            try:
                token = Token.objects.get(key=request.COOKIES.get('authToken', ''))
                if IS_LENTACH:
                    return HttpResponseRedirect('/%s' % token.user.nickname)
                else:
                    return HttpResponseRedirect('/feed')
            except Token.DoesNotExist:
                pass
        elif request.path.lower().startswith(('/feed', '/manage')) and not request.COOKIES.get('authToken'):
            return HttpResponseRedirect('/')
        return super(BaseTemplateView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(BaseTemplateView, self).get_context_data(**kwargs)
        ctx['debug'] = DEBUG
        return ctx


class ArticleView(DetailView):
    queryset = Article.objects.filter(status=Article.PUBLISHED)
    template_name = 'article.html'
    context_object_name = 'article'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        article = self.get_object()
        ctx = super(ArticleView, self).get_context_data(**kwargs)
        description = None
        if len(article.content.get('blocks')) and article.content['blocks'][0].get('type') == ArticleContentType.LEAD:
            description = article.content['blocks'][0].get('value')
        ctx['description'] = description
        im = article.content.get('cover_clipped') or article.content.get('cover')
        ctx['image'] = self.request.build_absolute_uri(im['image']) if im and im.get('image')else None
        ctx['url'] = self.request.build_absolute_uri(reverse('article', kwargs={'slug': article.slug}))
        ctx['debug'] = DEBUG
        return ctx


class EditorView(DetailView):
    queryset = Article.objects.filter(status__in=[Article.DRAFT, Article.PUBLISHED])
    template_name = 'editor.html'


def handler404(request):
    response = render_to_response('index.html', context=RequestContext(request))
    response.status_code = 404
    return response


def handler500(request):
    response = render_to_response('index.html', context=RequestContext(request))
    response.status_code = 500
    return response