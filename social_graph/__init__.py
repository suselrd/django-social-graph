from django.conf import settings
from .api import Graph, TO_NODE as TO_NODE_INDEX, ATTRIBUTES as ATTRIBUTES_INDEX, TIME as TIME_INDEX
from .decorators import crud_aware

# DECORATE the get_object() method for DetailView generic class, to send object_visited signal

DETAIL_VIEW_SEND_VISITED_SIGNAL = getattr(settings, 'DETAIL_VIEW_SEND_VISITED_SIGNAL', True)

if DETAIL_VIEW_SEND_VISITED_SIGNAL:

    from django.views.generic import DetailView

    normal_method = getattr(DetailView, 'get')

    def get(self, request, *args, **kwargs):
        from .signals import object_visited
        result = normal_method(self, request, *args, **kwargs)
        if Graph.is_registered_type(self.object.__class__):
            object_visited.send(self.object.__class__, instance=self.object, user=request.user)
        return result

    setattr(DetailView, 'get', get)
