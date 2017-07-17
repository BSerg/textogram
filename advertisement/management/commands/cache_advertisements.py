from django.core.management.base import BaseCommand

from advertisement.cache_utils import update_advertisements_cache


class Command(BaseCommand):
    help = 'Cache advertisements'

    def handle(self, *args, **options):
        update_advertisements_cache()
