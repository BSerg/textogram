import requests
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.generic.base import View

from textogram.settings import YANDEX_APP_ID, YANDEX_PASSWORD


class YandexAuthorization(View):
    CODE_URL = 'https://oauth.yandex.ru/authorize?response_type=code&client_id={client_id}'

    def get(self, request, *args, **kwargs):
        r = requests.get(self.CODE_URL.format(client_id=YANDEX_APP_ID))
        if r.status_code == 200:
            return HttpResponseRedirect(r.url)
        return HttpResponse('FAIL')


class YandexAuthorizationCallback(View):
    URL = 'https://oauth.yandex.ru/token'
    # URL = 'https://oauth.yandex.ru/token?grant_type=authorization_code&code={code}&client_id={client_id}&client_secret={client_secret}'

    def get(self, request, *args, **kwargs):
        print request.GET
        if request.GET.get('code'):
            r = requests.post(self.URL, data=dict(grant_type='authorization_code', code=request.GET['code'], client_id=YANDEX_APP_ID, client_secret=YANDEX_PASSWORD))
            if r.status_code == 200:
                return HttpResponse('ACCESS_TOKEN: ' + r.json()['access_token'])
        return HttpResponse('FAIL')

