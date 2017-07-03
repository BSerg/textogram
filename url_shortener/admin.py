from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import UrlShort


class UrlShortAdmin(admin.ModelAdmin):
    list_display = ['id', 'url', 'article', 'code', 'short_url', 'created_at']

    def id(self, obj):
        return obj.id

    def short_url(self, obj):
        return mark_safe('<a target="_blank" href="%(url)s">%(url)s</a>' % {'url': obj.get_short_url()})

admin.site.register(UrlShort, UrlShortAdmin)
