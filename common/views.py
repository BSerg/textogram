#! coding: utf-8

from __future__ import unicode_literals

from django.http.response import HttpResponse
from django.views import View

from common.models import RobotsRules


class RobotsView(View):
    def get(self, request, *args, **kwargs):
        robots = RobotsRules.objects.filter(is_active=True).first()
        if robots:
            return HttpResponse(robots.text, status=200, content_type='text/plain')
        return HttpResponse(status=404)
