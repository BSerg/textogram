from django.views.generic.detail import DetailView
from .models import UrlShort

from django.views.generic.base import RedirectView

from django.http.response import HttpResponsePermanentRedirect
from django.http.response import HttpResponseRedirect

# Create your views here.


class UrlShortDetailView(DetailView):
    model = UrlShort
    slug_field = 'code'
    slug_url_kwarg = 'code'

    def get(self, request, *args, **kwargs):

        url_short = self.get_object()
        url_short.count += 1
        url_short.save()
        return HttpResponseRedirect(url_short.url)

