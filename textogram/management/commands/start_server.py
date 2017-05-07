import os

import bjoern
import signal
from django.core.management import BaseCommand

from textogram.wsgi import application

worker_pids = []


class Command(BaseCommand):
    help = 'Start bjoern server'

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            type=str,
            dest='host',
            default='127.0.0.1',
            help='Host',
        )
        parser.add_argument(
            '--port',
            type=int,
            dest='port',
            default=8000,
            help='Port',
        )
        parser.add_argument(
            '--workers',
            type=int,
            dest='workers',
            default=1,
            help='Number of workers',
        )

    def handle(self, *args, **options):
        bjoern.listen(application, options['host'], options['port'])
        for _ in xrange(options['workers']):
            pid = os.fork()
            if pid > 0:
                worker_pids.append(pid)
            elif pid == 0:
                try:
                    bjoern.run()
                except KeyboardInterrupt:
                    pass
                exit()

        try:
            for _ in xrange(options['workers']):
                os.wait()
        except KeyboardInterrupt:
            for pid in worker_pids:
                os.kill(pid, signal.SIGINT)

