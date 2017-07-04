#! coding: utf-8

from __future__ import unicode_literals

import base64

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from articles.models import Article
from payments import walletone_get_signature
from payments.models import PayWallOrder
from textogram.settings import WMI_SECRET_KEY, WMI_MERCHANT_ID, WMI_CURRENCY_MAP, WMI_FORM_ACTION


class WalletOneFormView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        article_id = request.query_params.get('article_id')
        if not article_id:
            return Response({'msg': 'ArticleID query parameter havn\'t been passed'}, status=HTTP_400_BAD_REQUEST)
        try:
            article = Article.objects.get(pk=article_id)
        except Article.DoesNotExist:
            return Response({'msg': 'Article not found'}, status=HTTP_404_NOT_FOUND)

        order = PayWallOrder.create_new(article, request.user)

        if not order:
            return Response({'msg': 'There was an error on order creating'}, status=HTTP_400_BAD_REQUEST)

        form = {
            'WMI_MERCHANT_ID': WMI_MERCHANT_ID,
            'WMI_PAYMENT_AMOUNT': article.paywall_price,
            'WMI_CURRENCY_ID': WMI_CURRENCY_MAP[article.paywall_currency],
            'WMI_DESCRIPTION': 'BASE64:' + base64.b64encode(article.title.encode('utf-8')),
            'WMI_SUCCESS_URL': article.get_full_url(),
            'WMI_FAIL_URL': '',
            'WMI_PAYMENT_NO': order.id,
        }

        form['WMI_SIGNATURE'] = walletone_get_signature(form.items(), WMI_SECRET_KEY)

        return Response({'form': form, 'action': WMI_FORM_ACTION})

