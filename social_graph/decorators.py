# coding=utf-8


def crud_aware(cls):
    from social_graph.api import Graph
    Graph.register_node_type(cls)
    return cls
