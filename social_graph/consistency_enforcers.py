# coding=utf-8
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.db.models import F
from social_graph.api import Graph
from social_graph.models import EdgeTypeAssociation, Edge, EdgeCount, EdgeType


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
                                     type=symmetric_type)
                except ObjectDoesNotExist:
                    graph = Graph()
                    graph.edge_add(instance.toNode, instance.fromNode, symmetric_type, instance.attributes, auto=True)
            except ObjectDoesNotExist:
                pass

    @staticmethod
    def delete_symmetric_edge(sender, instance, **kwargs):
        try:
            symmetric_type = EdgeTypeAssociation.objects.get(direct=instance.type).inverse
            graph = Graph()
            graph.edge_delete(instance.toNode, instance.fromNode, symmetric_type)
        except ObjectDoesNotExist:
            pass


class SymmetricEdgeTypeAssociationManager(object):
    @staticmethod
    def create_symmetric_association(sender, instance, created, **kwargs):
        try:
            EdgeTypeAssociation.objects.get(direct=instance.inverse,
                                            inverse=instance.direct)
        except ObjectDoesNotExist:
            symmetric = EdgeTypeAssociation(direct=instance.inverse,
                                            inverse=instance.direct)
            symmetric.save()

    @staticmethod
    def delete_symmetric_association(sender, instance, **kwargs):
        try:
            symmetric = EdgeTypeAssociation.objects.get(direct=instance.inverse,
                                                        inverse=instance.direct)
            symmetric.delete()
        except ObjectDoesNotExist:
            pass


class EdgeCounter(object):
    @staticmethod
    def increase_count(sender, instance, created, **kwargs):
        counter, is_new = EdgeCount.objects.get_or_create(
            fromNode_pk=instance.fromNode.pk,
            fromNode_type=ContentType.objects.get_for_model(instance.fromNode),
            type=instance.type,
            defaults={
                'count': 1
            }
        )
        if not is_new:
            counter.count = F('count') + 1
            counter.save()
    @staticmethod
    def decrease_count(sender, instance, **kwargs):
        counter, is_new = EdgeCount.objects.get_or_create(fromNode_pk=instance.fromNode.pk,
                                                          fromNode_type=ContentType.objects.get_for_model(instance.fromNode),
                                                          type=instance.type)
        if not is_new:  # is_new case should never happen!!
            counter.count = F('count') - 1
            counter.save()


class EdgeCleaner(object):
    @staticmethod
    def clean_edges(sender, instance, **kwargs):
        if sender in (Edge, EdgeType, EdgeTypeAssociation, EdgeCount):
            return
        graph = Graph()
        types = EdgeType.objects.all()
        for etype in types:
            graph._edges_delete(instance, etype)