from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from articles.cache_utils import update_user_feed_cache, update_article_recommendations

from redis import Redis
from rq import Queue

from articles.models import Article
from textogram.settings import RQ_LOW_QUEUE, RQ_HOST, RQ_PORT, RQ_DB, RQ_TIMEOUT


class Command(BaseCommand):
    help = 'Cache article recommendations'

    def add_arguments(self, parser):
        parser.add_argument('slug', nargs='*')
        parser.add_argument(
            '-d', '--delete',
            action='store_true',
            dest='delete',
            default=False,
            help='Delete cached data of the slug',
        )

    def handle(self, *args, **options):
        q = Queue(RQ_LOW_QUEUE, connection=Redis(host=RQ_HOST, port=RQ_PORT, db=RQ_DB), default_timeout=RQ_TIMEOUT)
        slugs = options['slug'] or Article.objects.filter(status=Article.PUBLISHED).values_list('slug', flat=True)
        for slug in slugs:
            job = q.enqueue(update_article_recommendations, slug, options.get('delete'))
            self.stdout.write('Update article recommentations caching jobs created #%s' % job.id)

