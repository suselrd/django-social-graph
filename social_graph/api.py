# coding=utf-8
from time import mktime
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured
from django.core.cache import get_cache, DEFAULT_CACHE_ALIAS, InvalidCacheBackendError
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, post_delete
from django.db.transaction import atomic
from django.dispatch import receiver
from social_graph.models import Edge, EdgeCount
from social_graph import signals

GRAPH_CACHE_ALIAS = getattr(settings, 'GRAPH_CACHE_ALIAS', 'graph')

# KEY FORMATS
COUNT_KEY_FORMAT = getattr(settings, 'COUNT_KEY_FORMAT', "count:%(ctype)s:%(pk)s:%(etype)s")
EDGE_LIST_KEY_FORMAT = getattr(settings, 'EDGE_LIST_KEY_FORMAT', "elist:%(ctype)s:%(pk)s:%(etype)s")
EDGE_KEY_FORMAT = getattr(settings, 'EDGE_KEY_FORMAT', "edge:%(ctype1)s:%(pk1)s:%(etype)s:%(ctype2)s:%(pk2)s")


# EDGE LIST ITEM REPRESENTATION INDEX
TO_NODE = 0
ATTRIBUTES = 1
TIME = 2


class Graph(object):
    client_requires = [
        'pipeline',
        'add_to_sorted_set',
        'rem_from_sorted_set',
        'sorted_set_rev_range',
        'sorted_set_rev_range_by_score'
    ]
    __instance = None
    _nodeTypes = set()
    _instance_count = 0

    def __init__(self):
        try:
            self.cache = get_cache(GRAPH_CACHE_ALIAS)
        except InvalidCacheBackendError:
            self.cache = get_cache(DEFAULT_CACHE_ALIAS)
        for func_name in self.client_requires:
            if not getattr(self.cache, func_name, None):
                raise ImproperlyConfigured("Selected Cache backend must have a %s function" % func_name)

    def __new__(cls, *more):
        return cls.get_instance(*more)

    @classmethod
    def get_instance(cls, *more):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls, *more)
            cls._instance_count += 1
        return cls.__instance

    # Node Types Registry

    @staticmethod
    def register_node_type(model):
        Graph._nodeTypes.add(model)

    @staticmethod
    def unregister_node_type(model):
        try:
            Graph._nodeTypes.remove(model)
        except KeyError:
            pass

    @staticmethod
    def is_registered_type(model):
        return model in Graph._nodeTypes

    # Nodes Writing

    #noinspection PyUnusedLocal
    @staticmethod
    @receiver(post_save)
    def _node_save(sender, instance, created, **kwargs):
        """

        :param sender:
        :param instance:
        :param created:
        :param kwargs:
        """
        if not sender in Graph._nodeTypes:
            return
        if created:
            signals.object_created.send(sender=sender, instance=instance)
        else:
            signals.object_updated.send(sender=sender, instance=instance)

    #noinspection PyUnusedLocal
    @staticmethod
    @receiver(post_delete)
    def _node_delete(sender, instance, **kwargs):
        if not sender in Graph._nodeTypes:
            return
        signals.object_deleted.send(sender=sender, instance=instance)

    # Edges Writing
    @atomic
    def edge_add(self, from_node, to_node, etype, attributes="{}", auto=False):
        edge = Edge.objects.create(fromNode=from_node, toNode=to_node, type=etype, attributes=attributes, auto=auto)
        # write to cache, find all cached values that this new edge impacts on, and update them
        ctype1 = ContentType.objects.get_for_model(from_node)
        ctype2 = ContentType.objects.get_for_model(to_node)
        edge_key = (EDGE_KEY_FORMAT
                    % {'ctype1': ctype1.pk,
                       'pk1': from_node.pk,
                       'etype': etype.pk,
                       'ctype2': ctype2.pk,
                       'pk2': to_node.pk})
        count_key = (COUNT_KEY_FORMAT
                     % {'ctype': ctype1.pk,
                        'pk': from_node.pk,
                        'etype': etype.pk})
        list_key = (EDGE_LIST_KEY_FORMAT
                    % {'ctype': ctype1.pk,
                       'pk': from_node.pk,
                       'etype': etype.pk})

        transaction = self.cache.pipeline()
        transaction.set(edge_key, edge)
        if count_key in self.cache:
            transaction.incr(count_key)
        if list_key in self.cache:
            edge_rep = (edge.toNode, edge.attributes, edge.time)
            transaction.add_to_sorted_set(list_key, edge_rep, mktime(edge.time.timetuple()))
        transaction.execute()
        signals.edge_created.send(sender=etype, instance=edge)
        return edge

    @atomic
    def edge_change(self, from_node, to_node, etype, attributes):
        ctype1 = ContentType.objects.get_for_model(from_node)
        ctype2 = ContentType.objects.get_for_model(to_node)
        try:
            edge = Edge.objects.get(fromNode_pk=from_node.pk, fromNode_type=ctype1, toNode_pk=to_node.pk,
                                    toNode_type=ctype2, type=etype)
        except ObjectDoesNotExist:
            return self.edge_add(from_node, to_node, etype, attributes)
        edge.delete()
        # delete from cache: find all cached values that this new edge impacts on, and update them
        edge_key = (EDGE_KEY_FORMAT
                    % {'ctype1': ctype1.pk,
                       'pk1': from_node.pk,
                       'etype': etype.pk,
                       'ctype2': ctype2.pk,
                       'pk2': to_node.pk})
        list_key = (EDGE_LIST_KEY_FORMAT
                    % {'ctype': ctype1.pk,
                       'pk': from_node.pk,
                       'etype': etype.pk})

        transaction = self.cache.pipeline()
        if list_key in self.cache:
            edge_rep = (edge.toNode, edge.attributes, edge.time)
            transaction.rem_from_sorted_set(list_key, edge_rep)

        new_edge = Edge.objects.create(fromNode=from_node, toNode=to_node, type=etype, attributes=attributes)

        transaction.set(edge_key, new_edge)
        if list_key in self.cache:
            edge_rep = (new_edge.toNode, new_edge.attributes, new_edge.time)
            transaction.add_to_sorted_set(list_key, edge_rep, mktime(new_edge.time.timetuple()))
        transaction.execute()

        signals.edge_updated.send(sender=etype, instance=new_edge)
        return new_edge

    @atomic
    def edge_delete(self, from_node, to_node, etype):
        ctype1 = ContentType.objects.get_for_model(from_node)
        ctype2 = ContentType.objects.get_for_model(to_node)
        edge = Edge.objects.get(fromNode_pk=from_node.pk, fromNode_type=ctype1, toNode_pk=to_node.pk,
                                toNode_type=ctype2, type=etype)
        edge.delete()
        # delete from cache: find all cached values that this edge impacts on, and update them
        edge_key = (EDGE_KEY_FORMAT
                    % {'ctype1': ctype1.pk,
                       'pk1': from_node.pk,
                       'etype': etype.pk,
                       'ctype2': ctype2.pk,
                       'pk2': to_node.pk})
        count_key = (COUNT_KEY_FORMAT
                     % {'ctype': ctype1.pk,
                        'pk': from_node.pk,
                        'etype': etype.pk})
        list_key = (EDGE_LIST_KEY_FORMAT
                    % {'ctype': ctype1.pk,
                       'pk': from_node.pk,
                       'etype': etype.pk})
        transaction = self.cache.pipeline()
        transaction.delete(edge_key)
        if count_key in self.cache:
            transaction.decr(count_key)
        if list_key in self.cache:
            edge_rep = (edge.toNode, edge.attributes, edge.time)
            transaction.rem_from_sorted_set(list_key, edge_rep)
        transaction.execute()
        signals.edge_deleted.send(sender=etype, instance=edge)
        return True

    @atomic
    def _edges_delete(self, from_node, etype):
        ctype1 = ContentType.objects.get_for_model(from_node)
        edges = Edge.objects.filter(fromNode_pk=from_node.pk, fromNode_type=ctype1, type=etype)
        edges.delete()
        # delete from cache: find all cached values that this edges impacts on, and delete them
        count_key = (COUNT_KEY_FORMAT
                     % {'ctype': ctype1.pk,
                        'pk': from_node.pk,
                        'etype': etype.pk})
        list_key = (EDGE_LIST_KEY_FORMAT
                    % {'ctype': ctype1.pk,
                       'pk': from_node.pk,
                       'etype': etype.pk})

        if list_key in self.cache:
            count = self.edge_count(from_node, etype)
            edge_list = self.cache.sorted_set_rev_range(list_key, 0, count)
            transaction = self.cache.pipeline()
            for node, attributes, time in edge_list:
                ctype2 = ContentType.objects.get_for_model(node)
                edge_key = (EDGE_KEY_FORMAT
                            % {'ctype1': ctype1.pk,
                               'pk1': from_node.pk,
                               'etype': etype.pk,
                               'ctype2': ctype2.pk,
                               'pk2': node.pk})
                transaction.delete(edge_key)
            transaction.delete(list_key)
            transaction.delete(count_key)
            transaction.execute()
        elif count_key in self.cache:
            self.cache.delete(count_key)
        return True

    # Edges Reading

    def edge_count(self, from_node, etype):

        """
        Returns the number of edges of type etype that originate at from_node
        :param from_node:
        :param etype:
        :return: int
        """
        ctype = ContentType.objects.get_for_model(from_node)
        key = COUNT_KEY_FORMAT % {
            'ctype': ctype.pk,
            'pk': from_node.pk,
            'etype': etype.pk
        }
        count = self.cache.get(key)
        if count is None:
            try:
                count = EdgeCount.objects.get(fromNode_pk=from_node.pk, fromNode_type=ctype, type=etype).count
            except ObjectDoesNotExist:
                count = 0
            self.cache.set(key, int(count))
        return count

    def edge_range(self, from_node, etype, pos, limit):

        """
        Returns elements of the (from_node, etype) edge list with index i ∈ [pos, pos + limit).
        :param from_node:
        :param etype:
        """
        ctype = ContentType.objects.get_for_model(from_node)
        # check if the count is already cached
        count_key = (COUNT_KEY_FORMAT
                     % {'ctype': ctype.pk,
                        'pk': from_node.pk,
                        'etype': etype.pk})
        count = self.cache.get(count_key, None)
        list_key = (EDGE_LIST_KEY_FORMAT
                    % {'ctype': ctype.pk,
                       'pk': from_node.pk,
                       'etype': etype.pk})
        if count != 0 or count is None:  # the edge list must be checked
            edges = self.cache.sorted_set_rev_range(list_key, pos, limit)
            if len(edges) != 0:
                return edges
            else:
                edge_list = Edge.objects.filter(fromNode_pk=from_node.pk, fromNode_type=ctype, type=etype)
                transaction = self.cache.pipeline()
                for edge in edge_list:
                    edge_key = (EDGE_KEY_FORMAT
                                % {'ctype1': ctype.pk,
                                   'pk1': from_node.pk,
                                   'etype': etype.pk,
                                   'ctype2': edge.toNode_type.pk,
                                   'pk2': edge.toNode_pk})
                    edge_rep = (edge.toNode, edge.attributes, edge.time)
                    transaction.add_to_sorted_set(list_key, edge_rep, mktime(edge.time.timetuple()))
                    transaction.set(edge_key, edge)
                transaction.execute()
                return self.cache.sorted_set_rev_range(list_key, pos, limit)

        else:  # if count is zero, the list is empty
            return []

    def edges_get(self, from_node, etype, to_node_set):

        """
        Returns all of the edges (from_node, etype, to_node) and their time and data, where to_node ∈ to_node_set
        NOT VERY EFFICIENT!, USE CAREFULLY
        :param from_node:
        :param etype:
        :param to_node_set:
        """
        ctype = ContentType.objects.get_for_model(from_node)
        result = []
        to_look = []
        if not isinstance(to_node_set, list):
            to_node_set = [to_node_set]
        for node in to_node_set:
            ctype2 = ContentType.objects.get_for_model(node)
            edge_key = (EDGE_KEY_FORMAT
                        % {'ctype1': ctype.pk,
                           'pk1': from_node.pk,
                           'etype': etype.pk,
                           'ctype2': ctype2.pk,
                           'pk2': node.pk})
            edge = self.cache.get(edge_key, None)
            if edge:
                edge_rep = (edge.toNode, edge.attributes, edge.time)
                result.append(edge_rep)
            else:
                to_look.append(node)
        if len(to_look):
            edges = Edge.objects.filter(fromNode_pk=from_node.pk, fromNode_type=ctype, type=etype)
            list_key = (EDGE_LIST_KEY_FORMAT
                        % {'ctype': ctype.pk,
                           'pk': from_node.pk,
                           'etype': etype.pk})
            transaction = self.cache.pipeline()
            for edge in edges:
                edge_rep = (edge.toNode, edge.attributes, edge.time)
                transaction.add_to_sorted_set(list_key, edge_rep, mktime(edge.time.timetuple()))
                edge_key = (EDGE_KEY_FORMAT
                            % {'ctype1': edge.fromNode_type.pk,
                               'pk1': edge.fromNode_pk,
                               'etype': etype.pk,
                               'ctype2': edge.toNode_type.pk,
                               'pk2': edge.toNode_pk})
                transaction.set(edge_key, edge)
                if edge.toNode in to_look:
                    result.append(edge_rep)
            transaction.execute()
        return result

    def edge_time_range(self, from_node, etype, high, low, limit):
        """
        Returns elements from the (from_node, etype) edge list, starting with the first edge where time ≤ high,
        returning only edges where time ≥ low
        :param from_node:
        :param etype:
        :param high:
        :param low:
        :param limit:
        """
        ctype = ContentType.objects.get_for_model(from_node)
        # check if the count is already cached
        count_key = (COUNT_KEY_FORMAT
                     % {'ctype': ctype.pk,
                        'pk': from_node.pk,
                        'etype': etype.pk})
        count = self.cache.get(count_key, None)
        list_key = (EDGE_LIST_KEY_FORMAT
                    % {'ctype': ctype.pk,
                       'pk': from_node.pk,
                       'etype': etype.pk})
        if count != 0 or count is None:  # the edge list must be checked
            edges = self.cache.sorted_set_rev_range_by_score(list_key, low, high, 0, limit)
            if len(edges) != 0:
                return edges
            else:
                edge_list = Edge.objects.filter(fromNode_pk=from_node.pk, fromNode_type=ctype, type=etype)
                transaction = self.cache.pipeline()
                for edge in edge_list:
                    edge_key = (EDGE_KEY_FORMAT
                                % {'ctype1': ctype.pk,
                                   'pk1': from_node.pk,
                                   'etype': etype.pk,
                                   'ctype2': edge.toNode_type.pk,
                                   'pk2': edge.toNode_pk})
                    edge_rep = (edge.toNode, edge.attributes, edge.time)
                    transaction.add_to_sorted_set(list_key, edge_rep, mktime(edge.time.timetuple()))
                    transaction.set(edge_key, edge)
                transaction.execute()
                return self.cache.sorted_set_rev_range_by_score(list_key, low, high, 0, limit)
        else:  # if count is zero, the list is empty
            return []

    # Utils

    def clear_cache(self):
        self.cache.clear()