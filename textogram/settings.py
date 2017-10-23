"""
Django settings for textogram project.

Generated by 'django-admin startproject' using Django 1.10.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'k_$dafcqpr^b=oz$0u2d3erkb95ew@_z6w(ql=k-^$6)m3zz8q'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'polymorphic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'rest_framework',
    'storages',
    'sorl.thumbnail',
]

INSTALLED_APPS += [
    'textogram',
    'accounts',
    'common',
    'articles',
    'notifications',
    'advertisement',
    'url_shortener',
    'frontend',
    'statistics',
    'payments',
]

MIDDLEWARE = [
    # 'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'textogram.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'frontend.processors.extra_context_processor',
                'frontend.processors.is_bot_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'textogram.wsgi.application'

SITE_ID = 1

IS_LENTACH = False

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'

MEDIA_URL = '/data/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'accounts.auth.AuthServiceBackend',
    'django.contrib.auth.backends.ModelBackend'
]

AUTH_PUBLIC_KEY = None

AUTH_SERVICE_ROOT = ''
AUTH_SERVICE_VERIFY_API = ''
AUTH_SERVICE_REFRESH_API = ''
AUTH_SERVICE_SSL_VERIFY = False

# REST

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'accounts.auth.JWTAuthentication'
    ),
    'DEFAULT_THROTTLE_RATES': {
        'search': '60/min',
        'image_upload': '1000/day'
    }
}

REST_FRAMEWORK_EXTENSIONS = {
    'DEFAULT_CACHE_RESPONSE_TIMEOUT': 60 * 15,
}

# SOCIALS

VK_APP_ID = ''
VK_APP_SECRET = ''
VK_ACCESS_TOKEN = ''
VK_REDIRECT_URI = ''

TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_KEY_SECRET = ''
TWITTER_ACCESS_TOKEN = ''
TWITTER_ACCESS_TOKEN_SECRET = ''

FACEBOOK_APP_ID = ''
FACEBOOK_APP_SECRET = ''
FACEBOOK_ACCESS_TOKEN = ''
FACEBOOK_LOGIN = ''
FACEBOOK_PASSWORD = ''
FACEBOOK_REDIRECT_URI = ''

GOOGLE_CLIENT_ID = ''
GOOGLE_API_KEY = ''

# Thumbnails

THUMBNAIL_QUALITY = 90

THUMBNAIL_LARGE_SIZE = '1900x1900'
THUMBNAIL_REGULAR_SIZE = '1200x1200'
THUMBNAIL_MEDIUM_SIZE = '600x600'
THUMBNAIL_SMALL_SIZE = '300x300'
THUMBNAIL_TINY_SIZE = '150x150'

# CONTENT SETTINGS

BANNER_DENSITY = 0.5

# ARTICLE NEW AGE, HOURS

NEW_ARTICLE_AGE = 24

# RQ

RQ_HIGH_QUEUE = 'high'
RQ_LOW_QUEUE = 'low'
RQ_QUEUES = [RQ_HIGH_QUEUE, RQ_LOW_QUEUE]
RQ_HOST = 'localhost'
RQ_PORT = 6379
RQ_DB = 0
RQ_TIMEOUT = 60 * 10

# Search bot list

BOT_USER_AGENTS = [
    'aolbuild',
    'baidu',
    'bingbot',
    'bingpreview',
    'msnbot',
    'duckduckgo',
    'adsbot-google',
    'googlebot',
    'mediapartners-google',
    'teoma',
    'slurp',
    'yandex'
]

FORBIDDEN_NICKNAMES = [
    'admin\w*',
    'api',
    'articles?',
    'drafts',
    'id\d+',
    'feed',
    'login',
    'logout',
    'manage',
    'manager',
    'nick',
    'nickname',
    'nickname\w+',
    'check_nickname',
    '\d\w*',

]

# Yandex API

YANDEX_APP_ID = ''
YANDEX_PASSWORD = ''
YANDEX_ACCESS_TOKEN = ''
YANDEX_CALLBACK_URL = ''

YANDEX_METRICS_COUNTER_ID = ''

GOOGLE_ANALYTICS_COUNTER_ID = ''

# Paywall

PAYWALL_ENABLED = False

PAYWALL_CURRENCY_USD = 'USD'
PAYWALL_CURRENCY_RUR = 'RUR'
PAYWALL_CURRENCY_EUR = 'EUR'
PAYWALL_CURRENCIES = (
    (PAYWALL_CURRENCY_RUR, 'Ruble'),
    (PAYWALL_CURRENCY_USD, 'US Dollar'),
    (PAYWALL_CURRENCY_EUR, 'Euro'),
)

USE_REDIS_CACHE = False
REDIS_CACHE_PORT = 6379
REDIS_CACHE_HOST = '127.0.0.1'
REDIS_CACHE_DB = 0
REDIS_CACHE_KEY_PREFIX = 't'


PAYMENT_TEST = False

# Wallet one

WMI_MERCHANT_ID = ''
WMI_CURRENCY_MAP = {
    'RUR': 643,
    'USD': 840,
    'EUR': 978
}
WMI_SECRET_KEY = ''
WMI_FORM_ACTION = 'https://wl.walletone.com/checkout/checkout/Index'

# Yandex kassa

YK_SHOP_ID = ''
YK_SCID = ''
YK_SECRET = ''


YK_FORM_ACTION = 'https://money.yandex.ru/eshop.xml'

# Recommendations

ARTICLE_RECOMMENDATIONS_MAX_COUNT = 10

try:
    from local_settings import *
except ImportError:
    pass
