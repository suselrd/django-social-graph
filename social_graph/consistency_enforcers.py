# coding=utf-8
from django.contrib.contenttypes.models import ContentType
from django.db.models import F
from social_graph.api import Graph
from social_graph.models import EdgeTypeAssociation, Edge, EdgeCount, EdgeType


graph = Graph()


class SymmetricEdgeManager(object):

    @staticmethod
    def create_symmetric_edge(sender, instance, created, **kwargs):
        if not instance.auto:
            try:
                symmetric_type = EdgeTypeAssociation.objects.get(direct=instance.type).inverse
                try:
                    Edge.objects.get(fromNode_pk=instance.toNode.pk,
                                     fromNode_type=ContentType.objects.get_for_model(instance.toNode),
                                     toNode_pk=instance.fromNode.pk,
                                     toNode_type=ContentType.objects.get_for_model(instance.fromNode),
                                     type=symmetric_type,
                                     site=instance.site)
                except Edge.DoesNotExist:
                    graph._add(instance.toNode, instance.fromNode, symmetric_type, instance.site, instance.attributes, auto=True)
            except EdgeTypeAssociation.DoesNotExist:
                pass

    @staticmethod
    def delete_symmetric_edge(sender, instance, **kwargs):
        try:
            symmetric_type = EdgeTypeAssociation.objects.get(direct=instance.type).inverse
            graph._delete(instance.toNode, instance.fromNode, symmetric_type, instance.site)
        except EdgeTypeAssociation.DoesNotExist:
            pass


class SymmetricEdgeTypeAssociationManager(object):
    @staticmethod
    def create_symmetric_association(sender, instance, created, **kwargs):
        try:
            EdgeTypeAssociation.objects.get(direct=instance.inverse,
                                            inverse=instance.direct)
        except EdgeTypeAssociation.DoesNotExist:
            symmetric = EdgeTypeAssociation(direct=instance.inverse,
                                            inverse=instance.direct)
            symmetric.save()

    @staticmethod
    def delete_symmetric_association(sender, instance, **kwargs):
        try:
            symmetric = EdgeTypeAssociation.objects.get(direct=instance.inverse,
                                                        inverse=instance.direct)
            symmetric.delete()
        except EdgeTypeAssociation.DoesNotExist:
            pass


class EdgeCounter(object):
    @staticmethod
    def increase_count(sender, instance, created, **kwargs):
        counter, is_new = EdgeCount.objects.get_or_create(
            fromNode_pk=instance.fromNode.pk,
            fromNode_type=ContentType.objects.get_for_model(instance.fromNode),
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
        counter, is_new = EdgeCount.objects.get_or_create(
            fromNode_pk=instance.fromNode.pk,
            fromNode_type=ContentType.objects.get_for_model(instance.fromNode),
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
        if sender in (Edge, EdgeType, EdgeTypeAssociation, EdgeCount):
            return
        types = EdgeType.objects.all()
        for etype in types:
            graph._delete_all(instance, etype)