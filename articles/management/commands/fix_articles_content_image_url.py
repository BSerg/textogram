from __future__ import unicode_literals

from django.core.management.base import BaseCommand, CommandError

from articles.models import Article
from articles.utils import process_content, content_to_html, fix_article_content_image_urls


class Command(BaseCommand):
    help = 'Update articles\' html code'

    def handle(self, *args, **options):
        for article in Article.objects.filter(content__isnull=False):
            fix_article_content_image_urls(article)
        self.stdout.write(self.style.SUCCESS('Articles successfully updated'))
