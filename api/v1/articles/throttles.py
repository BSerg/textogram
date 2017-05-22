#! coding: utf-8

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class SearchRateThrottle(UserRateThrottle):
    scope = 'search'


class ImageUploadRateThrottle(UserRateThrottle):
    scope = 'image_upload'



