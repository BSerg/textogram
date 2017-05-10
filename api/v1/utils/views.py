from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from articles.utils import EmbedHandlerError, get_handler


class EmbedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        url = request.data.get('url')
        type = request.data.get('type')
        if not url:
            raise ValidationError('URL is required')

        handler = get_handler(url, type=type)
        try:
            embed = handler.get_embed()
        except EmbedHandlerError:
            raise ValidationError('Embed process error')
        if not embed:
            raise ValidationError('URL was not processed correctly')
        return Response({'url': url, 'embed': embed, 'type': handler.get_type()})
