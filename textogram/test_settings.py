SECRET_KEY = 'fake-key'

AUTH_USER_MODEL = 'accounts.User'

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
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'textogram_test',
        'USER': 'postgres',
        'PASSWORD': 'admin'
    }
}

STATIC_URL = '/static/'
MEDIA_ROOT = '/home'

try:
    from local_test_settings import *
except ImportError:
    pass
