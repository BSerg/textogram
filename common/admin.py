from django.contrib import admin

from common.models import CounterCode, RobotsRules


class CounterCodeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']

admin.site.register(CounterCode, CounterCodeAdmin)


class RobotsRulesAdmin(admin.ModelAdmin):
    list_display = ['text', 'is_active']

admin.site.register(RobotsRules, RobotsRulesAdmin)
