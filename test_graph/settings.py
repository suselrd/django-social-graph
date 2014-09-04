# coding=utf-8

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'test',                        # Or path to database file if using sqlite3.
        'USER': 'postgres',                        # Not used with sqlite3.
        'PASSWORD': 'postgres',                   # Not used with sqlite3.
        'HOST': 'localhost',               # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5432',                        # Set to empty string for default. Not used with sqlite3.
    }
}

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': '127.0.0.1:6379',
    },
}

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'social_graph',
    'test_graph',
]

ROOT_URLCONF = 'test_graph.urls'

SITE_ID = 1

SECRET_KEY = 'blabla'