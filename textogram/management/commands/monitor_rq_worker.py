from __future__ import unicode_literals

import cmd
import os

from django.core.management.base import BaseCommand
from redis.client import StrictRedis
from rq import Connection, Worker
from rq import Queue
from rq.cli import info

from textogram import settings


class Command(BaseCommand):
    help = 'Monitoring rq worker'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        queues = Queue.all(StrictRedis(host=settings.RQ_HOST, port=settings.RQ_PORT, db=settings.RQ_DB))
        self.stdout.write('RQ Queues @ redis://%s:%d/%d' % (settings.RQ_HOST, settings.RQ_PORT, settings.RQ_DB))
        for q in queues:
            self.stdout.write('%-12s %d' % (q.name, q.count))

