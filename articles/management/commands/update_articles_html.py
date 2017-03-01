from __future__ import unicode_literals

from django.core.management.base import BaseCommand, CommandError

from articles.models import Article
from articles.utils import process_content, content_to_html


class Command(BaseCommand):
    help = 'Update articles\' html code'

    def handle(self, *args, **options):
        for article in Article.objects.filter(content__isnull=False):
            article.content = process_content(article.content)
            article.html = content_to_html(article.content)
            article.save()
        self.stdout.write(self.style.SUCCESS('Articles successfully updated'))
