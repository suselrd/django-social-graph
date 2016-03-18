# coding=utf-8

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'test',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'social_graph.cache_backend.ExtendedRedisCache',
        'LOCATION': ['127.0.0.1:6379'],
        'OPTIONS': {  # optional
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 2
            }
        },
    },
}

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'south',
    'social_graph',
    'test_graph',
]

ROOT_URLCONF = 'test_graph.urls'

SITE_ID = 1

SECRET_KEY = 'blabla'
