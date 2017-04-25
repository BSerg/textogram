from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from redis.client import StrictRedis
from rq import Connection, Worker
from textogram import settings


class Command(BaseCommand):
    help = 'Start rq worker'

    def add_arguments(self, parser):
        parser.add_argument('queues', nargs='*', type=str)

    def handle(self, *args, **options):
        with Connection(StrictRedis(host=settings.RQ_HOST, port=settings.RQ_PORT, db=settings.RQ_DB)):
            queues = options.get('queues') or ['default']
            w = Worker(queues)
            w.work()

