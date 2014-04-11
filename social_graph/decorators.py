# coding=utf-8
from social_graph.api import Graph


def crud_aware(cls):
    Graph.register_node_type(cls)
    return cls
