SECRET_KEY = 'fake-key'

INSTALLED_APPS = [
    'polymorphic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'react',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'storages',
    "accounts",
    "common",
    "articles",
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

STATIC_URL = '/static/'
MEDIA_ROOT = '/home'

try:
    from local_test_settings import *
except ImportError:
    pass
