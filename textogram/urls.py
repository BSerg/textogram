"""textogram URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap as sitemap_views
from django.views.decorators.cache import cache_page

from articles.sitemaps import ArticleSitemap
from textogram.settings import DEBUG, MEDIA_URL, MEDIA_ROOT
from url_shortener.views import UrlShortDetailView

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'', include('api.urls')),
    url(r'', include('frontend.urls')),
    url(r'^(?P<code>\w{4,})/?$', UrlShortDetailView.as_view(), name='short_url')
]

sitemaps = {
    'articles': ArticleSitemap
}

urlpatterns += [
    url(r'^sitemap\.xml$', cache_page(86400)(sitemap_views), {'sitemaps': sitemaps})
]

handler404 = 'frontend.views.handler404'
handler500 = 'frontend.views.handler500'


if DEBUG:
    urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)