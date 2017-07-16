#! coding: utf-8

from __future__ import unicode_literals

from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from advertisement.utils import serialize_banners


class BannersView(APIView):
    def get(self, request, *args, **kwargs):
        _banners = serialize_banners()
        if not _banners:
            return Response({'msg': 'Not Found'}, status=HTTP_404_NOT_FOUND)
        return Response(_banners)
