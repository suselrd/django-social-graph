# coding=utf-8
from django.conf.urls import *
from django.views.generic import DetailView
from test_graph.models import A, B


urlpatterns = patterns('',
                       (r'^a/(?P<pk>\d+)$', DetailView.as_view(model=A)),
                       (r'^b/(?P<pk>\d+)$', DetailView.as_view(model=B)),
)
