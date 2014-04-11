# coding=utf-8
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from social_graph.api import Graph
from social_graph.models import EdgeTypeAssociation, Edge, EdgeCount


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
                    graph.edge_add(instance.toNode, instance.fromNode, symmetric_type, auto=True)
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
        try:
            counter = EdgeCount.objects.get(fromNode_pk=instance.fromNode.pk,
                                            fromNode_type=ContentType.objects.get_for_model(instance.fromNode),
                                            type=instance.type)
        except ObjectDoesNotExist:  # when this is the first edge of this type created for a node
            counter = EdgeCount(fromNode=instance.fromNode,
                                type=instance.type)  # create a new counter with count 0
        counter.count += 1
        counter.save()
    @staticmethod
    def decrease_count(sender, instance, **kwargs):
        try:
            counter = EdgeCount.objects.get(fromNode_pk=instance.fromNode.pk,
                                            fromNode_type=ContentType.objects.get_for_model(instance.fromNode),
                                            type=instance.type)
            counter.count -= 1
        except ObjectDoesNotExist:  # this case should never happen
            counter = EdgeCount(fromNode=instance.fromNode,
                                type=instance.type)
        counter.save()