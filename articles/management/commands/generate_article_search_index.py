from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from articles.cache_utils import generate_search_index

from redis import Redis
from rq import Queue

from textogram.settings import RQ_LOW_QUEUE, RQ_HOST, RQ_PORT, RQ_DB, RQ_TIMEOUT


class Command(BaseCommand):
    help = 'Articles search index'

    def add_arguments(self, parser):
        parser.add_argument('article_id', nargs='?')

    def handle(self, *args, **options):
        q = Queue(RQ_LOW_QUEUE, connection=Redis(host=RQ_HOST, port=RQ_PORT, db=RQ_DB), default_timeout=RQ_TIMEOUT)
        job = q.enqueue(generate_search_index, options.get('article_id'))
        self.stdout.write('Search index #%s job created [%s]' % (options['article_id'], job.id))
