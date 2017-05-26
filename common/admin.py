from django.contrib import admin

from common.models import CounterCode


class CounterCodeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']

admin.site.register(CounterCode, CounterCodeAdmin)
