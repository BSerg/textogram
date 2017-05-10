#! coding: utf-8
from __future__ import unicode_literals
from django.contrib import admin

from advertisement.models import Banner, BannerGroup


class BannerInline(admin.StackedInline):
    model = Banner
    extra = 0


class BannerGroupAdmin(admin.ModelAdmin):
    list_display = ['identifier', 'get_banner_count', 'is_mobile', 'is_active']
    inlines = [BannerInline]
    list_filter = ['identifier', 'is_mobile', 'is_active']

    def get_banner_count(self, obj):
        return obj.banners.count()

    get_banner_count.short_description = 'Кол-во баннеров'


admin.site.register(BannerGroup, BannerGroupAdmin)
