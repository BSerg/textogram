from django.conf.urls import url, include


urlpatterns = [
    url(r'^v1/', include('api.v1.accounts.urls')),
    url(r'^v1/', include('api.v1.articles.urls')),
    url(r'^v1/', include('api.v1.notifications.urls')),
    url(r'^v1/', include('api.v1.utils.urls')),
    url(r'^v1/', include('api.v1.advertisement.urls')),
    url(r'^v1/', include('api.v1.url_shortener.urls')),
]
