from django.core.management.base import BaseCommand, CommandError

from accounts.cache_utils import update_user_cache


class Command(BaseCommand):
    help = 'Cache user'

    def add_arguments(self, parser):
        parser.add_argument('user_id', nargs='?')

    def handle(self, *args, **options):
        user_id = options['user_id'][0] if (options and options['user_id']) else None
        update_user_cache(user_id)
