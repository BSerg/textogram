from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from articles.cache_utils import update_user_feed_cache


from redis import Redis
from rq import Queue

from textogram.settings import RQ_LOW_QUEUE, RQ_HOST, RQ_PORT, RQ_DB, RQ_TIMEOUT


class Command(BaseCommand):
    help = 'Cache article feed'

    def add_arguments(self, parser):
        parser.add_argument('user_id')
        parser.add_argument('author_id')
        parser.add_argument('is_subscribed', default=False, nargs='?')

    def handle(self, *args, **options):
        print type(options.get('is_subscribed'))

        q = Queue(RQ_LOW_QUEUE, connection=Redis(host=RQ_HOST, port=RQ_PORT, db=RQ_DB), default_timeout=RQ_TIMEOUT)
        job = q.enqueue(update_user_feed_cache, options.get('user_id'),
                        options.get('author_id'), options.get('is_subscribed'))
        self.stdout.write('User feed update #%s job created [%s]' % (options.get('user_id'), job.id))
