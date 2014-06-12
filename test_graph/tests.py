from time import sleep, time
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group
from django import forms
from django.test import TestCase
from social_graph.api import Graph, TO_NODE, ATTRIBUTES
from social_graph.forms import BaseEdgeForm, SpecificTypeEdgeForm
from social_graph.models import EdgeType, EdgeTypeAssociation, Edge
from social_graph.signals import edge_created, edge_deleted, object_created, object_deleted, edge_updated, object_visited
from test_graph.models import A, B


class MyException(Exception):
    pass


#noinspection PyUnusedLocal
def raise_exception(**kwargs):
    raise MyException()


class SocialGraphTest(TestCase):
    def setUp(self):
        self.graph = Graph()
        self.graph.clear_cache()
        self.users = [User.objects.create(username="pepe")]
        self.objects = {
            'advanced': Group.objects.create(name="advanced users"),
            'admin': Group.objects.create(name="administrators"),
            'limited': Group.objects.create(name="limited users"),
            'dummy': Group.objects.create(name="dummy users")

        }
        self.relationships = {
            'like': EdgeType.objects.create(name="Like", read_as="likes"),
            'liked_by': EdgeType.objects.create(name="Liked By", read_as="is liked by")
        }
        EdgeTypeAssociation.objects.create(direct=self.relationships['like'], inverse=self.relationships['liked_by'])
        self.created_flag = False
        self.deleted_flag = False
        self.visited_flag = False

    def test_edge_type_creation_and_association(self):
        self.assertEqual(EdgeTypeAssociation.objects.count(), 2)
        self.assertEqual(EdgeTypeAssociation.objects.all()[1].direct, EdgeTypeAssociation.objects.all()[0].inverse)
        self.assertEqual(EdgeTypeAssociation.objects.all()[1].inverse, EdgeTypeAssociation.objects.all()[0].direct)

        EdgeTypeAssociation.objects.all()[0].delete()
        self.assertEqual(EdgeTypeAssociation.objects.count(), 0)

    def test_edge_add(self):
        self.graph.edge_add(self.users[0], self.objects['advanced'], self.relationships['like'])
        # check the edge list
        self.assertEqual(self.graph.edge_count(self.users[0], self.relationships['like']), 1)
        self.assertEqual(len(Edge.objects.filter(fromNode_pk=self.users[0].pk,
                                                 fromNode_type=ContentType.objects.get_for_model(self.users[0]),
                                                 type=self.relationships['like'])), 1)
        edges = self.graph.edge_range(self.users[0], self.relationships['like'], 0, 10)
        self.assertEqual(edges[0][TO_NODE].name, self.objects['advanced'].name)
        # check the inverse edge list
        self.assertEqual(self.graph.edge_count(self.objects['advanced'], self.relationships['liked_by']), 1)
        edges = self.graph.edge_range(self.objects['advanced'], self.relationships['liked_by'], 0, 10)
        self.assertEqual(edges[0][TO_NODE].username, self.users[0].username)

        # add another edge
        self.graph.edge_add(self.users[0], self.objects['admin'], self.relationships['like'])
        self.assertEqual(self.graph.edge_count(self.users[0], self.relationships['like']), 2)
        self.assertEqual(len(Edge.objects.filter(fromNode_pk=self.users[0].pk,
                                                 fromNode_type=ContentType.objects.get_for_model(self.users[0]),
                                                 type=self.relationships['like'])), 2)
        self.assertEqual(self.graph.edge_count(self.objects['admin'], self.relationships['liked_by']), 1)

    def test_edge_add_atomicity(self):
        edge_created.connect(raise_exception, Graph)
        try:
            self.graph.edge_add(self.users[0], self.objects['advanced'], self.relationships['like'])
        except MyException:
            # check the edge list
            self.assertEqual(self.graph.edge_count(self.users[0], self.relationships['like']), 0)
            self.assertEqual(len(Edge.objects.filter(fromNode_pk=self.users[0].pk,
                                                     fromNode_type=ContentType.objects.get_for_model(self.users[0]),
                                                     type=self.relationships['like'])), 0)
            self.assertEqual(self.graph.edge_range(self.users[0], self.relationships['like'], 0, 10), [])
            # check the inverse edge list
            self.assertEqual(self.graph.edge_count(self.objects['advanced'], self.relationships['liked_by']), 0)
            self.assertEqual(self.graph.edge_range(self.objects['advanced'], self.relationships['liked_by'], 0, 10), [])
        edge_created.disconnect(raise_exception, Graph)

    def test_edge_delete(self):
        self.graph.edge_add(self.users[0], self.objects['advanced'], self.relationships['like'])
        self.graph.edge_add(self.users[0], self.objects['admin'], self.relationships['like'])
        self.graph.edge_add(self.users[0], self.objects['limited'], self.relationships['like'])
        edges = self.graph.edge_range(self.users[0], self.relationships['like'], 0, 10)
        self.assertEqual(len(edges), 3)
        self.graph.edge_delete(self.users[0], self.objects['advanced'], self.relationships['like'])
        edges = self.graph.edge_range(self.users[0], self.relationships['like'], 0, 10)
        self.assertEqual(len(edges), 2)
        self.assertEqual(self.graph.edge_count(self.users[0], self.relationships['like']), 2)
        self.assertEqual(len(Edge.objects.filter(fromNode_pk=self.users[0].pk,
                                                 fromNode_type=ContentType.objects.get_for_model(self.users[0]),
                                                 type=self.relationships['like'])), 2)
        self.assertEqual(edges[0][TO_NODE].name, self.objects['limited'].name)
        self.assertEqual(edges[1][TO_NODE].name, self.objects['admin'].name)

    def test_edge_delete_atomicity(self):
        edge_deleted.connect(raise_exception, Graph)
        try:
            self.graph.edge_add(self.users[0], self.objects['advanced'], self.relationships['like'])
            self.graph.edge_delete(self.users[0], self.objects['advanced'], self.relationships['like'])
        except MyException:
            self.assertEqual(self.graph.edge_count(self.users[0], self.relationships['like']), 1)
            self.assertEqual(len(Edge.objects.filter(fromNode_pk=self.users[0].pk,
                                                     fromNode_type=ContentType.objects.get_for_model(self.users[0]),
                                                     type=self.relationships['like'])), 1)
        edge_deleted.disconnect(raise_exception, Graph)

    def test_edge_range_order(self):
        self.graph.edge_add(self.users[0], self.objects['advanced'], self.relationships['like'])
        sleep(1)
        self.graph.edge_add(self.users[0], self.objects['admin'], self.relationships['like'])
        sleep(1)
        self.graph.edge_add(self.users[0], self.objects['limited'], self.relationships['like'])
        edges = self.graph.edge_range(self.users[0], self.relationships['like'], 0, 10)
        self.assertEqual(edges[0][TO_NODE].name, self.objects['limited'].name)
        self.assertEqual(edges[1][TO_NODE].name, self.objects['admin'].name)
        self.assertEqual(edges[2][TO_NODE].name, self.objects['advanced'].name)

    def test_edge_time_range(self):
        t0 = time()
        sleep(1)
        self.graph.edge_add(self.users[0], self.objects['advanced'], self.relationships['like'])
        t1 = time()
        sleep(1)
        self.graph.edge_add(self.users[0], self.objects['admin'], self.relationships['like'])
        t2 = time()
        sleep(1)
        self.graph.edge_add(self.users[0], self.objects['limited'], self.relationships['like'])
        t3 = time()

        edges = self.graph.edge_time_range(self.users[0], self.relationships['like'], t0, t2, 10)
        self.assertEqual(len(edges), 2)
        self.assertEqual(edges[0][TO_NODE].name, self.objects['admin'].name)
        self.assertEqual(edges[1][TO_NODE].name, self.objects['advanced'].name)

        edges = self.graph.edge_time_range(self.users[0], self.relationships['like'], t0, t2, 1)
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0][TO_NODE].name, self.objects['admin'].name)

        edges = self.graph.edge_time_range(self.users[0], self.relationships['like'], t0, t1, 10)
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0][TO_NODE].name, self.objects['advanced'].name)

        edges = self.graph.edge_time_range(self.users[0], self.relationships['like'], t0, t3, 10)
        self.assertEqual(len(edges), 3)
        self.assertEqual(edges[0][TO_NODE].name, self.objects['limited'].name)
        self.assertEqual(edges[1][TO_NODE].name, self.objects['admin'].name)
        self.assertEqual(edges[2][TO_NODE].name, self.objects['advanced'].name)

    def test_edge_change(self):
        self.graph.edge_add(self.users[0], self.objects['advanced'], self.relationships['like'])

        self.assertEqual(self.graph.edge_count(self.users[0], self.relationships['like']), 1)
        self.assertEqual(len(Edge.objects.filter(fromNode_pk=self.users[0].pk,
                                                 fromNode_type=ContentType.objects.get_for_model(self.users[0]),
                                                 type=self.relationships['like'])), 1)
        self.assertEqual(self.graph.edge_range(self.users[0], self.relationships['like'], 0, 10)[0][ATTRIBUTES], {})

        self.graph.edge_change(self.users[0], self.objects['advanced'], self.relationships['like'], {"quantity": 3})

        self.assertEqual(self.graph.edge_count(self.users[0], self.relationships['like']),
                         len(self.graph.edge_range(self.users[0], self.relationships['like'], 0, 10)))
        self.assertEqual(len(Edge.objects.filter(fromNode_pk=self.users[0].pk,
                                                 fromNode_type=ContentType.objects.get_for_model(self.users[0]),
                                                 type=self.relationships['like'])),
                         len(self.graph.edge_range(self.users[0], self.relationships['like'], 0, 10)))
        self.assertEqual(Edge.objects.filter(fromNode_pk=self.users[0].pk,
                                             fromNode_type=ContentType.objects.get_for_model(self.users[0]),
                                             type=self.relationships['like'])[0].attributes,
                         {"quantity": 3})
        self.assertEqual(self.graph.edge_range(self.users[0], self.relationships['like'], 0, 10)[0][TO_NODE].name,
                         self.objects['advanced'].name)
        self.assertEqual(self.graph.edge_range(self.users[0], self.relationships['like'], 0, 10)[0][ATTRIBUTES],
                         {"quantity": 3})

    def test_edge_change_atomicity(self):
        edge_updated.connect(raise_exception, Graph)
        try:
            self.graph.edge_add(self.users[0], self.objects['advanced'], self.relationships['like'])
            self.graph.edge_change(self.users[0], self.objects['advanced'], self.relationships['like'], {"quantity": 3})
        except MyException:
            self.assertEqual(self.graph.edge_count(self.users[0], self.relationships['like']), 1)
            self.assertEqual(len(self.graph.edge_range(self.users[0], self.relationships['like'], 0, 10)), 1)
            self.assertEqual(len(Edge.objects.filter(fromNode_pk=self.users[0].pk,
                                                     fromNode_type=ContentType.objects.get_for_model(self.users[0]),
                                                     type=self.relationships['like'])), 1)
            self.assertEqual(self.graph.edge_range(self.users[0], self.relationships['like'], 0, 10)[0][ATTRIBUTES], {})
            self.assertEqual(Edge.objects.filter(fromNode_pk=self.users[0].pk,
                                                 fromNode_type=ContentType.objects.get_for_model(self.users[0]),
                                                 type=self.relationships['like'])[0].attributes, {})
        edge_updated.disconnect(raise_exception, Graph)

    def test_edges_get(self):
        self.graph.edge_add(self.users[0], self.objects['advanced'], self.relationships['like'])
        self.graph.edge_add(self.users[0], self.objects['limited'], self.relationships['like'])
        self.graph.edge_add(self.users[0], self.objects['admin'], self.relationships['like'])

        edges = self.graph.edges_get(self.users[0], self.relationships['like'],
                                     [self.objects['advanced'], self.objects['limited'], self.objects['dummy']])
        self.assertEqual(len(edges), 2)
        self.assertEqual(edges[0][TO_NODE].name, self.objects['advanced'].name)
        self.assertEqual(edges[1][TO_NODE].name, self.objects['limited'].name)

    #noinspection PyUnusedLocal
    def _created_flag_on(self, **kwargs):
        self.created_flag = True

    #noinspection PyUnusedLocal
    def _deleted_flag_on(self, **kwargs):
        self.deleted_flag = True

    #noinspection PyUnusedLocal
    def _visited_flag_on(self, **kwargs):
        self.visited_flag = True

    def test_model_with_crud_aware_decorator(self):
        object_created.connect(self._created_flag_on, A)
        object_deleted.connect(self._deleted_flag_on, A)
        object_visited.connect(self._visited_flag_on)

        self.assertEqual(self.created_flag, False)
        created = A.objects.create(a=5)
        self.assertEqual(self.created_flag, True)

        self.assertEqual(self.deleted_flag, False)
        created.delete()
        self.assertEqual(self.deleted_flag, True)

        self.assertEqual(self.visited_flag, False)
        obj = A.objects.create(a=55)
        from django.test.client import Client
        c = Client()
        response = c.get('/a/%s' % obj.id)
        self.assertIn('object', response.context_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.visited_flag, True)

        object_created.disconnect(self._created_flag_on, A)
        object_deleted.disconnect(self._deleted_flag_on, A)
        object_visited.disconnect(self._visited_flag_on)

    def test_model_without_crud_aware_decorator(self):
        object_created.connect(self._created_flag_on, B)
        object_deleted.connect(self._deleted_flag_on, B)
        object_visited.connect(self._visited_flag_on)

        self.assertEqual(self.created_flag, False)
        created = B.objects.create(b=5)
        self.assertEqual(self.created_flag, False)

        self.assertEqual(self.deleted_flag, False)
        created.delete()
        self.assertEqual(self.deleted_flag, False)

        self.assertEqual(self.visited_flag, False)
        obj = B.objects.create(b=55)
        from django.test.client import Client
        c = Client()
        response = c.get('/b/%s' % obj.id)
        self.assertIn('object', response.context_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.visited_flag, False)

        object_created.disconnect(self._created_flag_on, B)
        object_deleted.disconnect(self._deleted_flag_on, B)
        object_visited.disconnect(self._visited_flag_on)

    #noinspection PyProtectedMember
    def test_singleton(self):
        self.assertEqual(self.graph._instance_count, 1)
        Graph()
        self.assertEqual(self.graph._instance_count, 1)

    def test_edge_type_manager(self):
        id = self.relationships['like'].id
        name = self.relationships['like'].name
        # first time we call get()
        self.assertEqual(EdgeType.objects.get(name=name), self.relationships['like'])
        self.assertIn(id, EdgeType.objects._cache[EdgeType.objects.db])
        self.assertEqual(EdgeType.objects._cache[EdgeType.objects.db][id], self.relationships['like'])
        self.assertIn(name, EdgeType.objects._cache[EdgeType.objects.db])
        self.assertEqual(EdgeType.objects._cache[EdgeType.objects.db][name], self.relationships['like'])
        # from second time we call get() on, the edge type should be got from cache, without hitting the db
        self.assertEqual(EdgeType.objects.get(name=name), self.relationships['like'])
        self.assertEqual(EdgeType.objects.get(id=id), self.relationships['like'])
        self.assertEqual(EdgeType.objects.get(pk=id), self.relationships['like'])
        # clear cache
        EdgeType.objects.clear_cache()
        self.assertNotIn(EdgeType.objects.db, EdgeType.objects._cache)

        self.relationships['like'].delete()

    def test_edge_type_association_manager(self):
        association = EdgeTypeAssociation.objects.get_for_direct_edge_type(self.relationships['like'])
        self.assertEqual(association.inverse, self.relationships['liked_by'])
        self.assertIn(association.id, EdgeTypeAssociation.objects._cache[EdgeTypeAssociation.objects.db])
        self.assertEqual(EdgeTypeAssociation.objects._cache[EdgeTypeAssociation.objects.db][association.id], association)
        self.assertIn(association.direct.id, EdgeTypeAssociation.objects._direct_cache[EdgeTypeAssociation.objects.db])
        self.assertEqual(EdgeTypeAssociation.objects._direct_cache[EdgeTypeAssociation.objects.db][association.direct.id], association)
        self.assertIn(association.inverse.id, EdgeTypeAssociation.objects._inverse_cache[EdgeTypeAssociation.objects.db])
        self.assertEqual(EdgeTypeAssociation.objects._inverse_cache[EdgeTypeAssociation.objects.db][association.inverse.id], association)

    def test_edge_form_descendants(self):
        like = self.relationships['like']

        class LikeForm(BaseEdgeForm):
            edge_origin = 'user'
            edge_target = 'group'
            edge_attributes = ['rating', ]
            update = False

            user = forms.ModelChoiceField(User.objects.all())
            group = forms.ModelChoiceField(Group.objects.all())
            rating = forms.CharField()

            def get_etype(self):
                return like

        data = {
            'user': self.users[0].pk,
            'group': self.objects['advanced'].pk,
            'rating': '5',
        }

        form = LikeForm(dict(**data))
        self.assertTrue(form.is_valid())

        edge = form.save()

        # then check the edge list
        self.assertEqual(self.graph.edge_count(self.users[0], self.relationships['like']), 1)
        self.assertEqual(len(Edge.objects.filter(fromNode_pk=self.users[0].pk,
                                                 fromNode_type=ContentType.objects.get_for_model(self.users[0]),
                                                 type=self.relationships['like'])), 1)
        edges = self.graph.edge_range(self.users[0], self.relationships['like'], 0, 10)
        self.assertEqual(edges[0][TO_NODE].name, self.objects['advanced'].name)
        # and check the inverse edge list
        self.assertEqual(self.graph.edge_count(self.objects['advanced'], self.relationships['liked_by']), 1)
        edges = self.graph.edge_range(self.objects['advanced'], self.relationships['liked_by'], 0, 10)
        self.assertEqual(edges[0][TO_NODE].username, self.users[0].username)

    def test_specific_type_edge_form_descendants(self):
        like = self.relationships['like']

        class LikeForm(SpecificTypeEdgeForm):
            etype = like
            edge_origin = 'user'
            edge_target = 'group'
            edge_attributes = ['rating', 'favorite']
            update = False

            user = forms.ModelChoiceField(User.objects.all())
            group = forms.ModelChoiceField(Group.objects.all())
            rating = forms.CharField()
            favorite = forms.BooleanField()


        data = {
            'user': self.users[0].pk,
            'group': self.objects['advanced'].pk,
            'rating': '5',
            'favorite': True
        }

        form = LikeForm(dict(**data))
        self.assertTrue(form.is_valid())

        form.save()

        # then check the edge list
        self.assertEqual(self.graph.edge_count(self.users[0], self.relationships['like']), 1)
        self.assertEqual(len(Edge.objects.filter(fromNode_pk=self.users[0].pk,
                                                 fromNode_type=ContentType.objects.get_for_model(self.users[0]),
                                                 type=self.relationships['like'])), 1)
        edges = self.graph.edge_range(self.users[0], self.relationships['like'], 0, 10)
        self.assertEqual(edges[0][TO_NODE].name, self.objects['advanced'].name)
        self.assertEqual(edges[0][ATTRIBUTES], {'rating': '5', 'favorite': True})
        # and check the inverse edge list
        self.assertEqual(self.graph.edge_count(self.objects['advanced'], self.relationships['liked_by']), 1)
        edges = self.graph.edge_range(self.objects['advanced'], self.relationships['liked_by'], 0, 10)
        self.assertEqual(edges[0][TO_NODE].username, self.users[0].username)
        self.assertEqual(edges[0][ATTRIBUTES], {'rating': '5', 'favorite': True})


if __name__ == '__main__':
    import unittest
    unittest.main()
