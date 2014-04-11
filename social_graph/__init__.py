from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.views.generic import DetailView
from social_graph.api import Graph, TO_NODE, ATTRIBUTES, TIME
from social_graph.consistency_enforcers import SymmetricEdgeManager, SymmetricEdgeTypeAssociationManager, \
    EdgeCounter
from social_graph.models import Edge, EdgeTypeAssociation
from social_graph.signals import object_visited

# MAKE THE GRAPH API VISIBLE AT APP LEVEL

Graph = Graph
TO_NODE_INDEX = TO_NODE
ATTRIBUTES_INDEX = ATTRIBUTES
TIME_INDEX = TIME

# CONNECT LISTENERS TO ENFORCE GRAPH CONSISTENCY

post_save.connect(SymmetricEdgeManager.create_symmetric_edge, sender=Edge)
post_delete.connect(SymmetricEdgeManager.delete_symmetric_edge, sender=Edge)

post_save.connect(SymmetricEdgeTypeAssociationManager.create_symmetric_association, sender=EdgeTypeAssociation)
post_delete.connect(SymmetricEdgeTypeAssociationManager.delete_symmetric_association, sender=EdgeTypeAssociation)

post_save.connect(EdgeCounter.increase_count, sender=Edge)
post_delete.connect(EdgeCounter.decrease_count, sender=Edge)


# DECORATE the get_object() method for DetailView generic class, to send object_visited signal

DETAIL_VIEW_SEND_VISITED_SIGNAL = getattr(settings, 'DETAIL_VIEW_SEND_VISITED_SIGNAL', True)

if DETAIL_VIEW_SEND_VISITED_SIGNAL:
    normal_method = getattr(DetailView, 'get_object')

    def get_object(*args, **kwargs):
        result = normal_method(*args, **kwargs)
        if Graph.is_registered_type(result.__class__):
            object_visited.send(DetailView, instance=result)
        return result

    setattr(DetailView, 'get_object', get_object)
