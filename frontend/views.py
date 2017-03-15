from django.urls import reverse
from django.views.generic import DetailView

from articles import ArticleContentType
from articles.models import Article


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
            description = article.content['blocks'][0].get('value')[:200]
        ctx['description'] = description
        im = article.content.get('cover_clipped') or article.content.get('cover')
        ctx['image'] = self.request.build_absolute_uri(im['image']) if im and im.get('image')else None
        ctx['url'] = self.request.build_absolute_uri(reverse('article', kwargs={'slug': article.slug}))
        return ctx
