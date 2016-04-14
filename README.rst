==========================
Django Social Graph
==========================

Social graph for Django>=1.6.1


Changelog
=========

0.3.5
-----
Fixed edge update procedure (cache policy).

0.3.4
-----
Fixed edge cleaner.

0.3.3
-----
Temporarily invalidating edge lists from cache when one of its items must be excluded, until we figure out how to
get it done correctly.

0.3.2
-----
Added spanish translations
Included management commands to be packaged along with the application

0.3.1
-----
Added unique constraint to Edge model.
(Until now, this constraint have been enforced by api logic, but had some issues when cache contains residual items)

0.3.0
-----
Removed deprecated methods: edge_add(), edge_change(), and edge_delete(). --> BACKWARDS INCOMPATIBILITY
Uses django-redis-cache as a third party package, and creates a new extended redis cache backend.
General code refactoring (not loading so many stuff at init.py).
Minimized module level imports.
New management command clear_graph_cache

0.2.0
-----
Allows only one edge per node pair, edge type and site.
Deprecated old methods: edge_add(), edge_change(), and edge_delete(); introduced methods edge() and no_edge()
to substitute them. (Is not recommendable to mix old deprecated method usage with new method usage, can lead to inconsistent data!)
New edge_get() method to retrieve only one edge (if exists). (Is only safe to use when edge creation is handled by edge() method, not by deprecated edge_add/edge_change)

0.1.9
-----
Fixes in delete_edge behaviour (handling more corner case's exceptions)


0.1.8
-----
Fixes in multi-site support. CHANGED API METHODS SIGNATURES!!!!


0.1.7
-----
Full site aware implementation (Note: A different cache instance SHOULD be defined for each Site)


0.1.6
-----
More specific signal sender:
* object_visited sender is the model class


0.1.5
-----
New EdgeCleaner consistency enforcer, to erase all edges belonging to a deleted object.
Improvement in EdgeCounter consistency enforcers to make it thread safe.


0.1.4
-----

More specific signal senders: 
* object_created, object_updated and object_deleted sender is the model class
* edge_created, edge_updated and edge_deleted sender is the edge type


0.1.3
-----

Symmetric edges are now created with the same attributes as their original edges.

EdgeForm allows to set a list of "edge attribute" fields" from which it takes the corresponding values and builds the attributes dictionary for the edge to save.

0.1.2
-----

Added the BaseEdgeForm and the SpecificTypeEdgeForm, to be inherited by all forms that intend to save and Edge object.
This forms' save() operation uses the Graph api, instead of Django's ORM directly.

Added the authenticated user argument to the object_visited signal.

Api operations edge_add and edge_change now return the created/changed edge.
If the edge_change operation determine that the target edge doesn't exist, it automatically calls edge_add operation.

0.1.1
-----

EdgeType and EdgeTypeAssociation cache implementation, to prevent hitting the database unnecessarily to "get"
an EdgeType or EdgeTypeAssociation

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

