import bjoern
from django.core.management import BaseCommand

from textogram.wsgi import application


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

    def handle(self, *args, **options):
        bjoern.run(application, options['host'], options['port'])

