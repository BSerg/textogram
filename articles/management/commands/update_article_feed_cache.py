from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from articles.cache_utils import update_feed_cache

from redis import Redis
from rq import Queue

from textogram.settings import RQ_HIGH_QUEUE, RQ_HOST, RQ_PORT, RQ_DB, RQ_TIMEOUT


class Command(BaseCommand):
    help = 'Cache article feed'

    def add_arguments(self, parser):
        parser.add_argument('article_id', nargs='?')

    def handle(self, *args, **options):
        q = Queue(RQ_HIGH_QUEUE, connection=Redis(host=RQ_HOST, port=RQ_PORT, db=RQ_DB), default_timeout=RQ_TIMEOUT)
        job = q.enqueue(update_feed_cache, options['article_id'])
        self.stdout.write('Article #%s job created [%s]' % (options['article_id'], job.id))

        # update_feed_cache(options['article_id'])
