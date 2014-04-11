==========================
Django Social Graph
==========================

Social graph for Django>=1.6.1

Includes the implementation of django-redis-cache (by Sean Bleier).


Changelog
=========

0.1.0
-----

PENDING...

Notes
-----

Requires the `redis-py`_ Python client library for
communicating with the Redis server.

Redis writes to disk asynchronously so there is a slight chance
of losing some data, but for most purposes this is acceptable.

In order to use ``redis.connection.HiredisParser`` parser class, you need to
pip install `hiredis`_.  This is the recommended parser class.

Usage
-----

1. Run ``python setup.py install`` to install.

2. Modify your Django settings to use ``redis_cache`` for graph cache:

    # When using TCP connections
    CACHES = {
        'graph': {
            'BACKEND': 'redis_cache.RedisCache',
            'LOCATION': '<host>:<port>',
            'OPTIONS': {
                'DB': 1,
                'PASSWORD': 'yadayada',
                'PARSER_CLASS': 'redis.connection.HiredisParser',
                'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
                'CONNECTION_POOL_CLASS_KWARGS': {
                    'max_connections': 50,
                    'timeout': 20,
                }
            },
        },
    }

    # When using unix domain sockets
    # Note: ``LOCATION`` needs to be the same as the ``unixsocket`` setting
    # in your redis.conf
    CACHES = {
        'graph': {
            'BACKEND': 'redis_cache.RedisCache',
            'LOCATION': '/path/to/socket/file',
            'OPTIONS': {
                'DB': 1,
                'PASSWORD': 'yadayada',
                'PARSER_CLASS': 'redis.connection.HiredisParser'
            },
        },
    }

.. _redis-py: http://github.com/andymccurdy/redis-py/
.. _hiredis: https://github.com/pietern/hiredis-py

If you want to use redis_cache not only for graph cache, but as the default cache,
just configure the cache backend with the "default" alias, and the social graph will
use it as well.

3. Create edges types, and edge type associations; edges and start using the graph.

