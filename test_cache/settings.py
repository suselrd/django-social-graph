DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'redis_cache',
    'social_graph',
    'test_cache',
]

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

ROOT_URLCONF = 'test_cache.urls'

SECRET_KEY = 'blabla'
