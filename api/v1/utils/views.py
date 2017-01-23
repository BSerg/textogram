from __future__ import unicode_literals

import re

import requests
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from articles.utils import EmbedHandlerError, get_embed
from textogram.settings import VK_APP_ID, VK_APP_SECRET


class EmbedAPIView(APIView):
    permission_classes = [IsAuthenticated]

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


class VKAccessTokenView(APIView):
    permission_classes = [IsAuthenticated]

    AUTH_URL = 'https://oauth.vk.com/authorize?client_id=%(app_id)s&display=page&scope=friends&response_type=code&v=5.62'
    TOKEN_URL = 'https://oauth.vk.com/access_token?client_id=%(app_id)s&client_secret=%(secret)s&code=%(code)s'

    def get(self, request, *args, **kwargs):
        url = self.AUTH_URL % {'app_id': VK_APP_ID}
        auth_response = requests.get(url)
        if auth_response.status_code != 200:
            raise ValidationError('Authorize api is not available')
        print auth_response.content
        code_url = auth_response.url
        print code_url
        code_re = re.search(r'#code=(?P<code>\w+)', code_url)
        if code_re:
            code = code_re.group('code')
            token_response = requests.get(self.TOKEN_URL % {
                'app_id': VK_APP_ID,
                'secret': VK_APP_SECRET,
                'code': code
            })
            if token_response.status_code == 200:
                return Response(token_response.json())
        return Response('FAIL')