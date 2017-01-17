from __future__ import unicode_literals
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('social_links', views.SocialLinksViewSet)
router.register('users', views.PublicUserViewSet)
router.register('subscriptions', views.SubscriptionViewSet)

urlpatterns = [
    url(r'users/me/$', views.MeUserViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'})),
    url(r'logout/$', views.Logout.as_view()),
    url(r'registration/', views.Registration.as_view()),
    url(r'', include(router.urls))
]

