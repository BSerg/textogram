from __future__ import unicode_literals

from rest_framework import viewsets, mixins, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from articles import get_embed
from articles import EmbedHandlerError, get_embed


class EmbedAPIView(APIView):
    def post(self, request, *args, **kwargs):
        url = request.data.get('url')
        type = request.data.get('type')
        if not url:
            raise ValidationError('URL is required')
        try:
            embed = get_embed(url, type=type)
        except EmbedHandlerError:
            raise ValidationError('Embed process error')
        if not embed:
            raise ValidationError('URL was not processed correctly')
        return Response({'url': url, 'embed': embed})