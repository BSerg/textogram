from django.core.management.base import BaseCommand, CommandError

from accounts.cache_utils import update_user_cache


class Command(BaseCommand):
    help = 'Cache user'

    def add_arguments(self, parser):
        parser.add_argument('user_id', nargs='?')

    def handle(self, *args, **options):
        update_user_cache(options.get('user_id'))
