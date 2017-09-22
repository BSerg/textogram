from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from redis import Redis
from rq import Queue

from articles.cache_utils import update_article_access
from articles.models import ArticleUserAccess
from textogram.settings import RQ_LOW_QUEUE, RQ_HOST, RQ_PORT, RQ_DB, RQ_TIMEOUT


class Command(BaseCommand):
    help = 'Cache article access'

    def add_arguments(self, parser):
        parser.add_argument('access_id', nargs='*')
        parser.add_argument(
            '-d', '--delete',
            action='store_true',
            dest='delete',
            default=False,
            help='Delete cached data of the slug',
        )

    def handle(self, *args, **options):
        q = Queue(RQ_LOW_QUEUE, connection=Redis(host=RQ_HOST, port=RQ_PORT, db=RQ_DB), default_timeout=RQ_TIMEOUT)
        accesses = options['access_id'] or ArticleUserAccess.objects.all().values_list('id', flat=True)

        for access_id in accesses:
            job = q.enqueue(update_article_access, access_id, options['delete'])
            self.stdout.write('Update article access caching jobs created #%s' % job.id)
