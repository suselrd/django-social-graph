# coding=utf-8


class SymmetricEdgeManager(object):

    @staticmethod
    def create_symmetric_edge(sender, instance, created, **kwargs):
        from .models import EdgeTypeAssociation, Edge
        if not instance.auto:
            try:
                symmetric_type = EdgeTypeAssociation.objects.get(direct=instance.type).inverse
                try:
                    Edge.objects.get(fromNode_pk=instance.toNode.pk,
                                     fromNode_type_id=instance.toNode_type_id,
                                     toNode_pk=instance.fromNode.pk,
                                     toNode_type_id=instance.fromNode_type_id,
                                     type=symmetric_type,
                                     site=instance.site)
                except Edge.DoesNotExist:
                    from .api import Graph
                    Graph()._add(
                        instance.toNode,
                        instance.fromNode,
                        symmetric_type,
                        instance.site,
                        instance.attributes,
                        auto=True
                    )
            except EdgeTypeAssociation.DoesNotExist:
                pass

    @staticmethod
    def delete_symmetric_edge(sender, instance, **kwargs):
        from .models import EdgeTypeAssociation
        try:
            symmetric_type = EdgeTypeAssociation.objects.get(direct=instance.type).inverse
            from .api import Graph
            Graph()._delete(instance.toNode, instance.fromNode, symmetric_type, instance.site)
        except EdgeTypeAssociation.DoesNotExist:
            pass


class SymmetricEdgeTypeAssociationManager(object):
    @staticmethod
    def create_symmetric_association(sender, instance, created, **kwargs):
        from .models import EdgeTypeAssociation
        try:
            EdgeTypeAssociation.objects.get(direct=instance.inverse,
                                            inverse=instance.direct)
        except EdgeTypeAssociation.DoesNotExist:
            symmetric = EdgeTypeAssociation(direct=instance.inverse,
                                            inverse=instance.direct)
            symmetric.save()

    @staticmethod
    def delete_symmetric_association(sender, instance, **kwargs):
        from .models import EdgeTypeAssociation
        try:
            symmetric = EdgeTypeAssociation.objects.get(direct=instance.inverse,
                                                        inverse=instance.direct)
            symmetric.delete()
        except EdgeTypeAssociation.DoesNotExist:
            pass


class EdgeCounter(object):
    @staticmethod
    def increase_count(sender, instance, created, **kwargs):
        from django.db.models import F
        from .models import EdgeCount
        counter, is_new = EdgeCount.objects.get_or_create(
            fromNode_pk=instance.fromNode_pk,
            fromNode_type_id=instance.fromNode_type_id,
            type=instance.type,
            site=instance.site,
            defaults={
                'count': 1
            }
        )
        if not is_new:
            counter.count = F('count') + 1
            counter.save()

    @staticmethod
    def decrease_count(sender, instance, **kwargs):
        from django.db.models import F
        from .models import EdgeCount
        counter, is_new = EdgeCount.objects.get_or_create(
            fromNode_pk=instance.fromNode_pk,
            fromNode_type_id=instance.fromNode_type_id,
            type=instance.type,
            site=instance.site,
            defaults={
                'count': 0
            }
        )
        if not is_new:  # is_new case should never happen!!
            counter.count = F('count') - 1
            counter.save()


class EdgeCleaner(object):
    @staticmethod
    def clean_edges(sender, instance, **kwargs):
        from social_graph.models import EdgeTypeAssociation, Edge, EdgeCount, EdgeType
        if sender in (Edge, EdgeType, EdgeTypeAssociation, EdgeCount):
            return
        types = EdgeType.objects.all()
        for e_type in types:
            from .api import Graph
            Graph()._delete_all(instance, e_type)
