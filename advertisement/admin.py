from django.contrib import admin

from advertisement.models import Banner


class BannerAdmin(admin.ModelAdmin):
    list_display = ['identifier', 'is_mobile', 'description', 'weight', 'is_active']

admin.site.register(Banner, BannerAdmin)
