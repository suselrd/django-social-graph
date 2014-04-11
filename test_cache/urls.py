from django.conf.urls import *


urlpatterns = patterns('',
    (r'^$', 'test_cache.views.someview'),
)