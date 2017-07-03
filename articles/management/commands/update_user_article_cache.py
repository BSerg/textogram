from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from articles.cache_utils import update_user_article_cache
from accounts.models import User

from redis import Redis
from rq import Queue

from textogram.settings import RQ_LOW_QUEUE, RQ_HOST, RQ_PORT, RQ_DB, RQ_TIMEOUT


class Command(BaseCommand):
    help = 'User articles cache'

    def add_arguments(self, parser):
        parser.add_argument('user_id', nargs='?')

    def handle(self, *args, **options):
        q = Queue(RQ_LOW_QUEUE, connection=Redis(host=RQ_HOST, port=RQ_PORT, db=RQ_DB), default_timeout=RQ_TIMEOUT)
        try:
            job = q.enqueue(update_user_article_cache, User.objects.get(id=options.get('user_id')))
            self.stdout.write('User articles #%s job created [%s]' % (options['user_id'], job.id))
        except (User.DoesNotExist, ValueError, TypeError):
            pass
