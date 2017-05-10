from __future__ import unicode_literals
from django.contrib import admin

from advertisement.models import Banner, BannerGroup


class BannerInline(admin.StackedInline):
    model = Banner
    extra = 0


class BannerGroupAdmin(admin.ModelAdmin):
    list_display = ['identifier', 'is_mobile', 'is_active']
    inlines = [BannerInline]


admin.site.register(BannerGroup, BannerGroupAdmin)
